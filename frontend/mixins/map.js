export const zoomToLanguage = ({ map, lang }) => {
  if (!map) return
  const bounds = [lang.bbox.coordinates[0][0], lang.bbox.coordinates[0][2]]
  map.fitBounds(bounds, { padding: 30 })
  map.setFilter('fn-lang-areas-highlighted', ['in', 'name', lang.name])
}

export const zoomToPoint = ({ map, geom, zoom }) => {
  console.log(geom.coordinates)
  map.flyTo({
    center: geom.coordinates,
    zoom: zoom || 10,
    speed: 3
  })
}

export const inBounds = (bounds, lnglat) => {
  let lng
  const multLng = (lnglat[0] - bounds._ne.lng) * (lnglat[0] - bounds._sw.lng)
  if (bounds._ne.lng > bounds._sw.lng) {
    lng = multLng < 0
  } else {
    lng = multLng > 0
  }
  const lat = (lnglat[1] - bounds._ne.lat) * (lnglat[1] - bounds._sw.lat) < 0
  return lng && lat
}

export const intersects = (r1, r2) => {
  return !(
    r2._sw.lng >= r1._ne.lng ||
    r2._ne.lng <= r1._sw.lng ||
    r2._ne.lat <= r1._sw.lat ||
    r2._sw.lat >= r1._ne.lat
  )
}
