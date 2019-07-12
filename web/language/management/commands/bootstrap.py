import pymysql
from django.core.management.base import BaseCommand, CommandError
from language.models import (
    Language, LanguageFamily, Community, LanguageSubFamily,
    Champion, PlaceName, Dialect, CommunityLink, LanguageLink)

import os
import sys
import json
from decimal import Decimal
from datetime import datetime
from django.contrib.gis.geos import Point

TABLE_MAP = {
    'tm_language_region': Language,
    'tm_language_subfamily': LanguageSubFamily,
    'tm_placename': PlaceName,
    'tm_champ': Champion,
    'tm_language_dialect': Dialect,
    'tm_language': LanguageFamily,
}


class DedruplifierClient:

    def query(self, sql):
        with self.db.cursor() as cursor:
            cursor.execute(sql)
            results = cursor.fetchall()
        return results

    def load(self):

        self.map_drupal_items('tm_language', LanguageFamily)

        self.map_drupal_items('tm_language_subfamily', LanguageSubFamily, {
            'field_language_family_target_id': 'family'
        })

        for rec, obj in self.map_drupal_items('tm_language_region', Language, {
            'field_tm_lang_subfam_target_id': 'sub_family',
            "field_tm_lr_colour_value": 'color',
            "field_tm_other_lang_names_value": 'other_names',
            "field_tm_lr_firstvoi_link_url": 'fv_archive_link',
            "field_tm_lr_state_note_value": "notes",
        }):
            for i, v in enumerate(rec.get('field_tm_lr_link_title',[])):
                title = rec['field_tm_lr_link_title'][i]
                url = rec['field_tm_lr_link_url'][i]
                LanguageLink.objects.get_or_create(
                    language=obj,
                    title=title,
                    url=url
                )

        for rec,obj in self.map_drupal_items('tm_fn_group', Community, {
            'field_tm_fn_grp_website_url': 'website',
            'field_tm_fn_comm_info_value': 'notes',
            'field_tm_fn_grp_alt_title_value': 'english_name',
            'field_tm_fn_lang_target_id': 'language',
            'field_tm_fn_internet_value': 'internet_speed',
            'field_tm_fn_latlong_lat': 'point',
            'field_tm_fn_total_pop_value': 'population',
            'field_tm_fn_grp_alt_title_value': 'other_names',
            'field_tm_fn_grp_email1_email': 'email',
            'field_tm_fn_grp_fax_value': 'fax',
            'field_tm_fn_grp_ph_tf_value': 'phone',
            'field_tm_fn_grp_ph_value': 'alt_phone',
        }):
            if rec.get('body_value',[''])[0].strip():
                obj.notes += "\n\n" + rec['body_value'][0]
            obj.save()

            for i, v in enumerate(rec.get('field_tm_fn_grp_links_title',[])):
                print('***',rec['field_tm_fn_grp_links_title'][i])
                title = rec['field_tm_fn_grp_links_title'][i]
                url = rec['field_tm_fn_grp_links_url'][i]
                CommunityLink.objects.get_or_create(
                    community=obj,
                    title=title,
                    url=url
                )

        self.map_drupal_items('tm_placename', PlaceName, {
            'field_tm_pn_othername_value': 'other_name',
            'field_tm_pn_location_lat': 'point',
        })

        self.map_drupal_items('tm_champ', Champion, {
            'field_tm_champ_bio_value': 'bio',
            'field_language_target_id': 'language',
            'field_tm_champ_occup_value': 'job',
            'field_tm_nation_target_id': 'community',
        })

        self.map_drupal_items('tm_language_dialect', Dialect, {
            'field_language_target_id': 'language',
        })


    def map_drupal_items(self, drupal_table, LocalTable, mapping={}):
        items = []
        drupal_data = json.loads(open('tmp/%s.json' % drupal_table).read())
        for pk, rec in drupal_data.items():
            #print(rec)
            try:
                item = LocalTable.objects.get(name=rec['title'])
            except LocalTable.DoesNotExist:
                item = LocalTable(name=rec['title'])
            for k, v in mapping.items():
                if k in rec:  # missing from data.
                    if k.endswith('target_id'):

                        FKTable = getattr(LocalTable, v).field.related_model
                        try:
                            obj = FKTable.objects.get(name=rec[k+'_title'][0])
                            setattr(item, v, obj)
                        except FKTable.DoesNotExist:
                            print(k, 'with pk',
                                  rec[k+'_title'], 'does not exist')
                        except KeyError:
                            print('WARN:', rec, 'has no', k+'_title')
                    elif k.endswith('_lat'):
                        pt = Point(rec[k][0], rec[k[:-4] + '_lon'][0])
                        setattr(item, v, pt)
                    else:
                        if len(rec[k]) > 1:
                            print(v, 'has', len(rec[k]))
                            setattr(item, v, ','.join(rec[k]))
                        else:
                            setattr(item, v, rec[k][0])
            item.save()
            items.append((rec, item))
            #print('saved', item)
        return items

    def update(self):
        self.db = pymysql.connect(
            os.environ['FPLM_HOST'],
            os.environ['FPLM_USER'],
            os.environ['FPLM_PW'],
            os.environ['FPLM_DB'],
            cursorclass=pymysql.cursors.DictCursor)

        """
        DeDruplify - remove the Drupal node schema with foreign fields and save flat JSON
        """
        nodes = self.query("select * from node;")
        _nodes = {}
        _by_id = {}
        for node in nodes:
            # "nid": 273, "vid": 330, "type": "tm_language", "language": "und", "title": "Wakashan", "uid": 1, "status": 1, "created": 1372273871, "changed": 1372273871, "comment": 0, "promote": 0, "sticky": 0, "tnid": 0, "translate": 0, "uuid"
            new_node = {
                'type': node['type'],
                'title': node['title'],
            }
            if node['type'] not in _nodes:
                _nodes[node['type']] = {}
            _nodes[node['type']][node['nid']] = new_node
            _by_id[node['nid']] = new_node
        for k, v in _nodes.items():
            print('type:', k, len(v))
        tables = [r['Tables_in_fpmaps_d7_live']
                  for r in self.query("show tables;")[:]]

        """
        mysql> select * from field_revision_field_tm_champ_link;
        +-------------+----------+---------+-----------+-------------+----------+-------+-------------------------+---------------------------+--------------------------------+
        | entity_type | bundle   | deleted | entity_id | revision_id | language | delta | field_tm_champ_link_url | field_tm_champ_link_title | field_tm_champ_link_attributes |
        +-------------+----------+---------+-----------+-------------+----------+-------+-------------------------+---------------------------+--------------------------------+
        | node        | tm_champ |       0 |      3476 |        3843 | und      |     0 | http://www.chrispaul.ca | NULL                      | a:0:{}                         |
        +-------------+----------+---------+-----------+-------------+----------+-------+-------------------------+---------------------------+--------------------------------+
        1 row in set (0.08 sec)
        """

        # flatten these dynamic fields into nice object lists.
        # man, what were we thinking in the late 90s...
        for table in tables:
            if table.startswith('field_data_'):
                print(table, 'being loaded.')
                for row in self.query('select * from %s' % table):
                    if row['entity_type'] != 'node':
                        continue

                    for k, v in row.items():
                        if k.startswith('field_') or 'value' in k and not k.endswith('_format'):
                            if type(v) is bytes:
                                #print('ignoring bytes', v)
                                continue
                            elif type(v) is Decimal:
                                v = float(v)
                            elif type(v) is datetime:
                                v = v.isoformat()
                            target = _nodes[row['bundle']][row['entity_id']]
                            if k not in target:
                                target[k] = []
                            if v not in target[k]: # add unique values to the list
                                target[k].append(v)

        # remap foreign keys using natural values (node titles)

        for pk, rec in _by_id.items():
            # print(rec)
            tmp = {}
            tmp.update(rec)
            for k, v in tmp.items():
                if k.endswith('target_id'):
                    rec[k+"_title"] = []
                    rec[k+"_type"] = []
                    for item in v:
                        if item in _by_id:
                            rec[k+"_title"].append(_by_id[item]['title'])
                            rec[k+"_type"].append(_by_id[item]['type'])
                        else:
                            rec[k+"_title"].append(None)
                            rec[k+"_type"].append(None)

        for typ, data in _nodes.items():
            #print(typ)

            open('tmp/{}.json'.format(typ),
                 'w').write(json.dumps(data, indent=4, sort_keys=True))


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):

        c = DedruplifierClient()
        #c.update()
        c.load()
