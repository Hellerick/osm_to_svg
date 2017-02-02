import xml.etree.ElementTree as ET
# https://docs.python.org/3/library/xml.etree.elementtree.html
osm_path = r'C:\Users\User\Dropbox\Job-shared\Conworlding\Opengeofiction\Latania\Latania.osm'
print(osm_path)
tree = ET.parse(osm_path)
print(tree)