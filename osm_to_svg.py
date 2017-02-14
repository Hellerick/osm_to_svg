import xml.etree.ElementTree as ET
import os
import platform
import re
import requests
from math import pi, log, tan

max_image_size = 1200
deg = pi / 180

# https://docs.python.org/3/library/xml.etree.elementtree.html


project_path = {
    'DESKTOP-62BVD4A': 'd:\KPV\Github\osm_to_svg',
    'hellerick-C17A': r'/home/hellerick/PycharmProjects/osm_to_svg'}[platform.node()]


example_osm_path = os.path.join(project_path, 'esunsoy.osm')

example_osm_path = 'd:\KPV\Maps\Moscow railroads\overpass-api.de - api - xapi - way bbox=36.7163086,55.0594952,38.0566406,56.1026834 railway=rail.osm'


def mercatorize(lat):
    lat *= deg
    y = log(tan(pi / 4 + lat / 2))
    return y / deg


def round3(n):
    return round(n*1000)/1000


class Bounds:
    def __init__(self, arg): # root=None, bounds=None
        if type(arg) == dict:
            bounds = arg
        else:
            root = arg
            try:
                bounds = root.find('bounds').attrib
            except AttributeError:
                nodes = root.findall('node')
                bounds = dict(
                        lat_min=min([float(n.attrib['lat']) for n in nodes]),
                        lat_max=max([float(n.attrib['lat']) for n in nodes]),
                        lon_min=min([float(n.attrib['lon']) for n in nodes]),
                        lon_max=max([float(n.attrib['lon']) for n in nodes]),
                    )
        self.bounds = bounds
        self.lat_min = float(bounds['lat_min'])
        self.lat_max = float(bounds['lat_max'])
        if self.lat_max < self.lat_min:
            self.lat_max += 360.0
        self.lon_min = float(bounds['lon_min'])
        self.lon_max = float(bounds['lon_max'])
        self.mer_max = mercatorize(self.lat_max)
        self.mer_min = mercatorize(self.lat_min)
        self.lon_ran = self.lon_max - self.lon_min
        self.lat_ran = self.lat_max - self.lat_min
        self.mer_ran = self.mer_max - self.mer_min
        if self.mer_ran > self.lon_ran:
            self.canvas = (1200.0 * self.lon_ran / self.mer_ran, 1200.0)
        else:
            self.canvas = (1200.0, 1200.0 * self.mer_ran / self.lon_ran)


class Node:
    def __init__(self, node, bounds):
        self.id = int(node.attrib['id'])
        self.lat = float(node.attrib['lat'])
        self.lon = float(node.attrib['lon'])
        self.mer = mercatorize(self.lat)
        self.x = (self.lon - bounds.lon_min) / bounds.lon_ran * bounds.canvas[0]
        self.y = bounds.canvas[1] - (self.mer - bounds.mer_min) / bounds.mer_ran * bounds.canvas[1]
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
        f'Bounds, lat: {bounds.lat_min:0.6f}..{bounds.lat_max:0.6f} ({bounds.lat_ran:0.6f}); '
        f'lon: {bounds.lon_min:0.6f}..{bounds.lon_max:0.6f} ({bounds.lon_ran:0.6f})')

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

# Downloading a certain type
# http://www.overpass-api.de/api/xapi?way[bbox=36.7163086,55.0594952,38.0566406,56.1026834][railway=rail]

def download_osm(bounds, selecttion):
    print('== Download OSM data ==')
    base_url = 'http://www.overpass-api.de/api/xapi?'
    query = f'way[bbox={bounds.lon_min},{bounds.lat_min},{bounds.lon_max},{bounds.lat_max}]'
    for key in selection:
        query = query + f'[{key}={selection[key]}]'
        print('Query:', base_url+query)
        osm_file_name = re.sub(r'(\[|\])+', ' ', query).strip()+'.osm'
        osm_file_path = os.path.join(project_path, osm_file_name)
        # osm_file_name = ''.join([c for c in query if c.isalnum() or c in ',.' else ' '])
        data = requests.get(base_url+query).text
        with open(osm_file_path, mode='wt', encoding='utf8') as f:
            f.write(data)
        print(f'Saved as: {osm_file_path}')
    return osm_file_path



if __name__ == '__main__':
    bounds = Bounds(dict(lon_min=35.1435, lon_max=40.2035, lat_min=54.2557, lat_max=56.9611))
    selection = {
        'railway': 'rail',
        # 'admin_level': '4',
    }
    osm_file_path = download_osm(bounds, selection)
    # generate_svg_from_osm(example_osm_path)
