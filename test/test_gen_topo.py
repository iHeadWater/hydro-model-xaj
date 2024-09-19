import hydromodel.datasets.gen_topo_txt as gtt
import geopandas as gpd

gpd_node_df = gpd.read_file(r'C:\Users\Administrator\IdeaProjects\hydrotopo\hydrotopo\test_data\near_changchun_dots.shp')
gpd_network_df = gpd.read_file(r'C:\Users\Administrator\IdeaProjects\hydrotopo\hydrotopo\test_data\near_changchun_cut.shp')

def test_gen_topo_txt():
    gtt.gen_topo_text_and_default_json(gpd_node_df, gpd_network_df, gpd_node_df.index.tolist())
