from factory.geometry_factory.geometry_factory import GeometryFactory


class GeometryHelper:

    @staticmethod
    def get_dummy_empty_geometry_handler():
        resolution = [10, 10, 10]
        spacing = [2, 2, 2]

        geometry_handler = GeometryFactory.get_geometry_handler(resolution, spacing)

        return geometry_handler
