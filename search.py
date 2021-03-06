from elasticsearch import Elasticsearch
from image_match.elasticsearch_driver import SignatureES


class WorkWithSignatures():
    n_grid = 9
    crop_percentile = (5, 95)
    P = None
    diagonal_neighbors = True
    identical_tolerance = 2 / 255
    n_levels = 2
    search_rotated = False

    es = Elasticsearch(
        ['elasticsearch'],
        port=9200,
    )


    ses = SignatureES(es, n_grid=n_grid, crop_percentile=crop_percentile, diagonal_neighbors=diagonal_neighbors,
                      identical_tolerance=identical_tolerance, n_levels=n_levels)

    def clear_db(self):
        self.es.indices.delete(index='images', ignore=[400, 404])
        self.es = Elasticsearch()
        self.ses = SignatureES(self.es, n_grid=self.n_grid, crop_percentile=self.crop_percentile,
                               diagonal_neighbors=self.diagonal_neighbors,
                               identical_tolerance=self.identical_tolerance, n_levels=self.n_levels)

    def reload_params(self, params):
        self.n_grid = params['n_grid']
        self.crop_percentile = params['crop_percentile']
        self.P = params['P']
        self.diagonal_neighbors = params['diagonal_neighbors']
        self.identical_tolerance = params['identical_tolerance']
        self.n_levels = params['n_levels']
        self.search_rotated = params['search_rotated']
        params.pop("search_rotated", None)
        self.ses = SignatureES(self.es, **params)

    def get_all_params(self):
        return {'n_grid': self.n_grid,
                'crop_percentile': self.crop_percentile,
                'P': self.P,
                'diagonal_neighbors': self.diagonal_neighbors,
                'identical_tolerance': self.identical_tolerance,
                'n_levels': self.n_levels,
                'search_rotated': self.search_rotated}

    def load_file(self, path):
        self.ses.add_image(path)

    def search_file(self, file_bytes):
        return self.ses.search_image(file_bytes, bytestream=True, all_orientations=self.search_rotated)
