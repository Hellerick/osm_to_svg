import xml.etree.ElementTree as ET
import os
import platform
import re
import requests
from math import pi, log, tan

max_image_size = 1200
deg = pi / 180
type_keys = {'railway', 'admin_level'}

stroke_colors = {
    'railway=rail': 'gray',
    'admin_level=4': 'red',
    'admin_level=5': 'orange',
}

# https://docs.python.org/3/library/xml.etree.elementtree.html


project_path = {
    'DESKTOP-62BVD4A': 'd:\KPV\Github\osm_to_svg',
    'hellerick-C17A': r'/home/hellerick/PycharmProjects/osm_to_svg'
}[platform.node()]


# example_osm_path = os.path.join(project_path, 'esunsoy.osm')

# example_osm_path = 'd:\KPV\Maps\Moscow railroads\overpass-api.de - api - ' \
#                    'xapi - way bbox=36.7163086,55.0594952,38.0566406,' \
#                    '56.1026834 railway=rail.osm'


def mercatorize(lat):
    lat *= deg
    y = log(tan(pi / 4 + lat / 2))
    return y / deg


def round3(n):
    return round(n*1000)/1000


class Bounds:
    def __init__(self, arg):
        if type(arg) == dict:
            arg_bounds = arg
        else:
            root = arg
            try:
                arg_bounds = root.find('bounds').attrib
            except AttributeError:
                nodes = root.findall('node')
                arg_bounds = dict(
                        lat_min=min([float(n.attrib['lat']) for n in nodes]),
                        lat_max=max([float(n.attrib['lat']) for n in nodes]),
                        lon_min=min([float(n.attrib['lon']) for n in nodes]),
                        lon_max=max([float(n.attrib['lon']) for n in nodes]),
                    )
        self.bounds = arg_bounds
        self.lat_min = float(arg_bounds['lat_min'])
        self.lat_max = float(arg_bounds['lat_max'])
        if self.lat_max < self.lat_min:
            self.lat_max += 360.0
        self.lon_min = float(arg_bounds['lon_min'])
        self.lon_max = float(arg_bounds['lon_max'])
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
    def __init__(self, node, arg_bounds):
        self.id = int(node.attrib['id'])
        self.lat = float(node.attrib['lat'])
        self.lon = float(node.attrib['lon'])
        self.mer = mercatorize(self.lat)
        self.x = ((self.lon - arg_bounds.lon_min) / arg_bounds.lon_ran *
                  arg_bounds.canvas[0])
        self.y = (arg_bounds.canvas[1] - (self.mer - arg_bounds.mer_min) /
                  arg_bounds.mer_ran * arg_bounds.canvas[1])
        self.plot = (self.x, self.y)


class Way:
    def __init__(self, way, nodes):
        self.id = int(way.attrib['id'])
        self.nd = [nodes[int(n.attrib['ref'])] for n in way.findall('nd')]
        self.d = "M " + ' L '.join(f'{round3(n.x)} {round3(n.y)}'
                                   for n in self.nd)

        try:
            # print('Way tag attribs:', way.findall('tag')[0].attrib)
            attributes = {t.attrib['k']: t.attrib['v']
                          for t in way.findall('tag')}
            for key in attributes:
                if key in type_keys:
                    self.type = f'{key}={attributes[key]}'
        except IndexError:
            self.type = 'none'


def generate_svg_from_osm(osm_path, arg_bounds):
    print('== SVG file generation ==')
    print('Argument:', osm_path)
    if type(osm_path) == list:
        tree = None
        for path in osm_path:
            print(f'Taken OSM: {path}')
            if tree is None:
                tree = ET.parse(path)
            else:
                new_tree = ET.parse(path)
                children = [c for c in new_tree._root]
                for c in children:
                    tree._root.append(c)
            print('Tree length:', len([c for c in tree._root]) )
        common_path = re.sub(
            r'\.osm\Z', '',
            max([
                osm_path[0][0:i]
                for i in range(len(osm_path[0])+1)
                if all([osm_path[0][0:i] in p for p in osm_path])
            ])
        )
    else:
        print(f'OSM file path: {osm_path}')
        common_path = re.sub(r'\.osm\Z', '', osm_path)
        tree = ET.parse(osm_path)
    root = tree.getroot()
    if arg_bounds is None:
        arg_bounds = Bounds(root)
    print(
        f'Bounds, '
        f'lat: {arg_bounds.lat_min:0.6f}..{arg_bounds.lat_max:0.6f} '
        f'({arg_bounds.lat_ran:0.6f}); '
        f'lon: {arg_bounds.lon_min:0.6f}..{arg_bounds.lon_max:0.6f} '
        f'({arg_bounds.lon_ran:0.6f})'
    )

    print('Canvas (width, height):', arg_bounds.canvas)

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
    ET.register_namespace(
        'inkscape', "http://www.inkscape.org/namespaces/inkscape")
    svg_canvas.set('xmlns', 'http://www.w3.org/2000/svg')
    svg_canvas.set(
        'xmlns:inkscape', 'http://www.inkscape.org/namespaces/inkscape')
    svg_canvas.set('version', '1.1')
    svg_canvas.set('width', str(round3(arg_bounds.canvas[0])))
    svg_canvas.set('height', str(round3(arg_bounds.canvas[1])))

    nodes = {
        int(n.attrib['id']): Node(n, arg_bounds)
        for n in root.findall('node')
        }

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
                ET.Element(
                    'path',
                    fill='none',
                    stroke=stroke_colors.get(l, 'black'),
                    d=ways[w].d
                )
                for w in ways if ways[w].type == l
            )
        )
        svg_canvas.extend([group])

    svg_path = common_path.strip()+'.svg'
    print(f'\nWriting SVG at\n{svg_path}')
    ET.ElementTree(svg_canvas).write(
        svg_path, xml_declaration=True, encoding='utf-8', method='xml'
    )


def download_osm(arg_bounds, arg_selection):
    print('== Download OSM data ==')
    base_url = 'http://www.overpass-api.de/api/xapi?'
    osm_file_paths = []
    for tag in arg_selection:
        query = (
            f'way[bbox={arg_bounds.lon_min},{arg_bounds.lat_min},'
            f'{arg_bounds.lon_max},{arg_bounds.lat_max}]'
            f'[{tag}]'
            )
        print(f'Query: {base_url+query}\n')
        osm_file_name = re.sub(r'(\[|\])+', ' ', query).strip()+'.osm'
        osm_file_path = os.path.join(project_path, osm_file_name)
        if os.path.exists(osm_file_path):
            print(
                f'The file at this path already exists and does not have to '
                f'be downloaded:\n'
                f'{osm_file_path}\n'
            )
        else:
            data = requests.get(base_url+query).text
            with open(osm_file_path, mode='wt', encoding='utf8') as f:
                f.write(data)
            print(f'The data downloaded and saved at:\n {osm_file_path}\n')
        osm_file_paths = osm_file_paths+[osm_file_path]
    return osm_file_paths


if __name__ == '__main__':
    bounds = Bounds(dict(lon_min=35.1435, lon_max=40.2035, lat_min=54.2557, lat_max=56.9611))
    selection = {
        'railway=rail',
        'admin_level=4',
        'admin_level=5',
    }
    osm_file_paths = download_osm(bounds, selection)
    generate_svg_from_osm(osm_file_paths, bounds)
