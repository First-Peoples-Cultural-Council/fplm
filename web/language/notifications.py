from users.models import User
import datetime

from language.models import PlaceName, Media, Favourite, CommunityMember

from django.db.models import Q
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

import re


def _format_fpcc(s):

    s = s.strip().lower()
    s = re.sub(
        r"\\|\/|>|<|\?|\)|\(|~|!|@|#|$|^|%|&|\*|=|\+|]|}|\[|{|\||;|:|_|\.|,|`|'|\"",
        "",
        s,
    )
    s = re.sub(r"\s+", "-", s)
    return s


def get_new_media_messages(new_medias):
    messages = []
    if new_medias.count():
        messages.append("<h3>New Media in Your Languages and Communities</h3><ul>")
        for media in new_medias:
            if media.placename:
                link = _place_link(media.placename)
            elif media.community:
                link = _comm_link(media.community)
            else:
                link = "(Orphaned Media)"
            preview = ''
            kind = 'media'
            if 'image' in media.file_type:
                link = ""
                kind = "image"
                preview = "<br><img src='{}/static/{}' width=100 style='width:100px;height:auto'/>".format(settings.HOST, media.media_file)
            if media.url:
                link = media.url
                kind = "video"
            messages.append(
                """
                <li>The location {} has a new media uploaded. {}</li>
            """.format(
                    link, preview
                )
            )

        messages.append("</ul>")
    return messages


def get_new_places_messages(new_places, scope="New Places"):
    messages = []
    if new_places.count():
        messages.append("<h3>{}</h3><ul>".format(scope))
        for place in new_places:
            link = _place_link(place)
            if place.creator:
                creator_name = str(place.creator)
            else:
                creator_name = "Someone"
            messages.append(
                """
                <li>{} uploaded a new place: {}.</li>
            """.format(
                    creator_name, link
                )
            )
        messages.append("</ul>")
    return messages


def get_my_favourites_messages(my_favourites):
    messages = []
    if my_favourites.count():
        messages.append("<h3>New Favourites</h3><ul>")
        for fav in my_favourites:
            if fav.place:
                link = _place_link(fav.place)
                messages.append(
                    """
                    <li>your place was favourited! {}</li>
                """.format(
                        link
                    )
                )
            else:
                link = _place_link(fav.media.placename)
                messages.append(
                    """
                    <li>your contribution was favourited! {}</li>
                """.format(
                        link
                    )
                )
        messages.append("</ul>")
    return messages


def _lang_link(l):
    return '<a href="{}/languages/{}">{}</a>'.format(
        settings.HOST, _format_fpcc(l.name), l.name
    )


def _comm_link(c):
    return '<a href="{}/content/{}">{}</a>'.format(
        settings.HOST, _format_fpcc(c.name), c.name
    )


def _place_link(p):
    return '<a href="{}/place-names/{}">{}</a>'.format(
        settings.HOST, _format_fpcc(p.name), p.name
    )


def notify(user, since=None):
    since = since or user.last_notified
    print("Calculating notifications for", user)
    intro = ["(We are in test mode, sending more data than you should actually receive, please let us know of any bugs!)"]

    languages = user.languages.all()
    communities = []
    communities_awaiting_verification = []
    for membership in CommunityMember.objects.filter(user=user):
        if membership.status == CommunityMember.VERIFIED:
            communities.append(membership.community)
        else:
            communities_awaiting_verification.append(membership.community)
    if languages.count():
        intro.append(
            "<p>You are receiving updates related to the following languages: {}</p>".format(
                ",".join([_lang_link(l) for l in languages])
            )
        )
    if len(communities):
        intro.append(
            "<p>You are receiving updates related to the following communities: {}</p>".format(
                ",".join([_comm_link(c) for c in communities])
            )
        )
    if len(communities_awaiting_verification):
        intro.append(
            "<p>You are still awaiting membership verification in the following communities: {}</p>".format(
                ",".join([_comm_link(c) for c in communities_awaiting_verification])
            )
        )
    messages = []
    # If somethe user is a member of a language, notify them of all the public places in their language of interest.
    for language in languages:
        new_places = PlaceName.objects.filter(
            ~Q(community__in=communities+communities_awaiting_verification), # don't double-show items in their community.
            language=language,
            community_only=False, created__gte=since)
        messages += get_new_places_messages(
            new_places, "New Places for the {} Language".format(language.name)
        )

    # all placenames, shared with verified members.
    for community in communities:
        new_places = PlaceName.objects.filter(community=community, created__gte=since)
        messages += get_new_places_messages(
            new_places, "New Places in {}".format(community.name)
        )

    # public placenames.
    for community in communities_awaiting_verification:
        new_places = PlaceName.objects.filter(community=community, created__gte=since, community_only=False)
        messages += get_new_places_messages(
            new_places, "New Places in {} (public updates only)".format(community.name)
        )


    # all media, shared only with verified members.
    new_medias_private = Media.objects.filter(
        Q(placename__community__in=communities),
        created__gte=since,
    )
    messages += get_new_media_messages(new_medias_private)


    # public media. Show public stuff to anyone who has signed up.
    new_medias_public = Media.objects.filter(
        Q(placename__language__in=languages) | Q(placename__community__in=communities_awaiting_verification),
        Q(community_only=False) & Q(placename__community_only=False), # public items.
        created__gte=since,
    )
    messages += get_new_media_messages(new_medias_public)

    my_favourites = Favourite.objects.filter(
        Q(media__creator=user) | Q(place__creator=user), created__gte=since
    )
    messages += get_my_favourites_messages(my_favourites)

    if len(messages):
        html = "\n".join(intro + messages)
        html += """
        <p>If you'd like to unsubscribe, change your notification settings <a href="{}/profile/edit/{}">here</a>.</p>
        """.format(
            settings.HOST, user.id
        )
        print(html)
        if user.email in [a[1] for a in settings.ADMINS]:
            print("sending to ", user.email)
            send_mail(
                "Your Updates on the First Peoples' Language Map",
                html,
                "info@fpcc.ca",
                [user.email],
                html_message=html,
            )
    else:
        print("No new information for this person.", intro)


def send():
    now = timezone.now()
    # find everyone who needs an update.
    users = User.objects.filter(
        # TODO: allow arbitrary notification frequency from account setting instead of hardcoding 7 here?
        last_notified__lte=now - datetime.timedelta(days=7),
        notification_frequency__gt=-1,
    )
    for user in users:

        notify(user)
        user.last_notified = now
        user.save()

