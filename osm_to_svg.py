import xml.etree.ElementTree as ET
import platform
import re
from math import pi, log, tan

max_image_size = 1200
deg = pi / 180

# https://docs.python.org/3/library/xml.etree.elementtree.html


example_osm_path = {
    'DESKTOP-62BVD4A': 'd:\KPV\Github\osm_to_svg\Vesunsoy.osm',
    'hellerick-C17A': r'/home/hellerick/PycharmProjects/osm_to_svg/Vesunsoy.osm'}[platform.node()]

# example_osm_path = '/home/hellerick/Dropbox/Job-shared/Conworlding/Opengeofiction/Latania/Latania.osm'


def mercatorize(lat):
    lat *= deg
    y = log(tan(pi / 4 + lat / 2))
    return y / deg


def round3(n):
    return round(n*1000)/1000


class Bounds:
    def __init__(self, root):
        bounds = root.find('bounds').attrib
        self.bounds = bounds
        self.latmin = float(bounds['minlat'])
        self.latmax = float(bounds['maxlat'])
        if self.latmax < self.latmin:
            self.latmax += 360.0
        self.lonmin = float(bounds['minlon'])
        self.lonmax = float(bounds['maxlon'])
        self.mermax = mercatorize(self.latmax)
        self.mermin = mercatorize(self.latmin)
        self.lonran = self.lonmax - self.lonmin
        self.latran = self.latmax - self.latmin
        self.merran = self.mermax - self.mermin
        if self.merran > self.lonran:
            self.canvas = (1200.0 * self.lonran / self.merran, 1200.0)
        else:
            self.canvas = (1200.0, 1200.0 * self.merran / self.lonran)


class Node:
    def __init__(self, node, bounds):
        self.id = int(node.attrib['id'])
        self.lat = float(node.attrib['lat'])
        self.lon = float(node.attrib['lon'])
        self.mer = mercatorize(self.lat)
        self.x = (self.lon - bounds.lonmin) / bounds.lonran * bounds.canvas[0]
        self.y = bounds.canvas[1] - (self.mer - bounds.mermin) / bounds.merran * bounds.canvas[1]
        self.plot = (self.x, self.y)


class Way:
    def __init__(self, way, nodes):
        self.id = int(way.attrib['id'])
        self.nd = [nodes[int(n.attrib['ref'])] for n in way.findall('nd')]
        self.d = "M " + ' L '.join(f'{round3(n.x)} {round3(n.y)}' for n in self.nd)

        try:
            # print('Way tag attribs:', way.findall('tag')[0].attrib)
            way_type = [t for t in way.findall('tag') if not t.attrib['k'] in ('source', 'name')][0]
            self.type = way_type.attrib['k']+' - '+way_type.attrib['v']
        except IndexError:
            self.type = 'none'


def generate_svg_from_osm(osm_path):
    print(f'OSM file path: {osm_path}')
    tree = ET.parse(osm_path)
    root = tree.getroot()
    bounds = Bounds(root)
    print(
        f'Bounds, lat: {bounds.latmin:0.6f}..{bounds.latmax:0.6f} ({bounds.latran:0.6f}); '
        f'lon: {bounds.lonmin:0.6f}..{bounds.lonmax:0.6f} ({bounds.lonran:0.6f})')

    print('Canvas (width, height):', bounds.canvas)

    # """ Visualize the structure """
    # print()
    # print('Content:')
    # for child in root[:10]:
    #     print(child.tag, child.attrib)
    #     for subchild in child:
    #         print(' >', subchild.tag, subchild.attrib)
    #         pass
    # print('...')

    '''Creating SVG'''
    svg_canvas = ET.Element('svg')
    ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")
    svg_canvas.set('xmlns', 'http://www.w3.org/2000/svg')
    svg_canvas.set('xmlns:inkscape', 'http://www.inkscape.org/namespaces/inkscape')
    svg_canvas.set('version', '1.1')
    svg_canvas.set('width', str(round3(bounds.canvas[0])))
    svg_canvas.set('height', str(round3(bounds.canvas[1])))

    nodes = {int(n.attrib['id']): Node(n, bounds) for n in root.findall('node')}
    # for i in range(1, 10):
    #     print(f'{i}, lat: {nodes[i].lat:0.6f}, lon: {nodes[i].lon:0.6f}, plot: {nodes[i].x:0.6f} {nodes[i].y:0.6f}')
    # nodes = {int(n.attrib['id']):(float(n.attrib['lat']), float(n.attrib['lon'])) for n in nodes}

    # mercatorize all nodes
    # nodes = {n:mercatorize(nodes[n]) for n in nodes}
    print('Nodes:', nodes)

    ways = {int(w.attrib['id']): Way(w, nodes) for w in root.findall('way')}

    way_layers = sorted(list({ways[w].type for w in ways}))
    print('Way layers:', way_layers)
    for l in way_layers:
        group = ET.Element('g')
        group.set('id', re.sub(' ', '_', l))
        group.set('inkscape:label', l)
        group.set('inkscape:groupmode', 'layer')
        group.extend(
                (
                    ET.Element('path', fill='none', stroke='black', d=ways[w].d)
                    for w in ways if ways[w].type == l
                )
            )
        svg_canvas.extend([group])

    # svg_canvas.extend([ET.Element('path', fill='none', stroke='black', d=ways[w].d) for w in ways])

    svg_path = osm_path+'.svg'
    print(f'\nWriting SVG at\n{svg_path}')
    ET.ElementTree(svg_canvas).write(svg_path, xml_declaration=True, encoding='utf-8', method='xml')
    # with open(svg_path, mode='wb') as svg_file:
    #
    #     svg_file.write(ET.tostring(svg_canvas))


if __name__ == '__main__':
    generate_svg_from_osm(example_osm_path)
