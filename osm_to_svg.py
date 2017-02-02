import xml.etree.ElementTree as ET
# https://docs.python.org/3/library/xml.etree.elementtree.html

example_osm_path = r'/home/hellerick/PycharmProjects/osm_to_svg/Vesunsoy.osm'

def generate_svg_from_osm(osm_path):
    print(f'OSM file path: {osm_path}')
    tree = ET.parse(osm_path)
    root = tree.getroot()
    for child in root:
        print(child.tag, child.attrib)
        for subchild in child:
            print(' >', subchild.tag, subchild.attrib)
    # print(tree)

if __name__ == '__main__':
    generate_svg_from_osm(example_osm_path)