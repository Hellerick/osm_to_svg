import xml.etree.ElementTree as ET
import platform
from math import pi, log, tan

max_image_size = 1200
deg = pi/180

# https://docs.python.org/3/library/xml.etree.elementtree.html


example_osm_path = {
    'DESKTOP-62BVD4A': 'd:\KPV\Github\osm_to_svg\Vesunsoy.osm',
    'Home': r'/home/hellerick/PycharmProjects/osm_to_svg/Vesunsoy.osm'}[	platform.node()]


def mercatorize(coords):
    lat = coords[0]*deg
    R = 1.0
    # lon0 = 0.0
    # x = R * (lon - lon0)
    y = R * log(tan(pi/4 + lat/2))
    return (y/deg, coords[1])


def generate_svg_from_osm(osm_path):
    print(f'OSM file path: {osm_path}')
    tree = ET.parse(osm_path)
    root = tree.getroot()
    global bounds
    bounds = root.find('bounds').attrib
    for key in bounds:
        try:
            bounds[key] = float(bounds[key])
        except ValueError: pass
    if bounds['maxlat'] < bounds['minlat']:
        bounds['maxlat'] = bounds['maxlat']+360.0
    bounds['avelat'] = (bounds['minlat']+bounds['maxlat'])/2
    bounds['avelon'] = (bounds['minlon']+bounds['maxlon'])/2
    bounds['maxmer'] = mercatorize((bounds['maxlat'],bounds['maxlon']))[0]
    bounds['minmer'] = mercatorize((bounds['minlat'],bounds['minlon']))[0]
    bounds['latrange'] = bounds['maxlat']-bounds['minlat']
    bounds['lonrange'] = bounds['maxlon']-bounds['minlon']
    bounds['merrange'] = bounds['maxmer']-bounds['minmer']
    print('Bounds:', bounds)

    # Canvas size: width, height
    if bounds['merrange'] > bounds['lonrange']:
        canvas = (1200.0*bounds['lonrange']/bounds['merrange'], 1200.0)
    else:
        canvas = (1200.0, 1200.0*bounds['merrange']/bounds['lonrange'])
    print('Canvas:', canvas)

    print()
    print('Content:')
    for child in root[:10]:
        print(child.tag, child.attrib)
        for subchild in child:
            print(' >', subchild.tag, subchild.attrib)
    print('...')

    nodes = root.findall('node')
    nodes = {int(n.attrib['id']):(float(n.attrib['lat']), float(n.attrib['lon'])) for n in nodes}
    print('Nodes:', nodes)

    # mercatorize all nodes

if __name__ == '__main__':
    generate_svg_from_osm(example_osm_path)