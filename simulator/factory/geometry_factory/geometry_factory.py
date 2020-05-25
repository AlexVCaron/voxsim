from numpy import array

from .features import Cluster, ClusterMeta, Bundle, Sphere
from .utils import Plane
from .handlers import GeometryHandler
from .utils import rotate_bundle, Rotation, translate_bundle


class GeometryFactory:
    """Factory class used to generate geometric primitives for simulations"""

    @staticmethod
    def get_geometry_handler(resolution, spacing):
        """
        Returns the handler in which all the primitives must be put in order to generate the
        json configuration file for voXSim.

        Parameters
        ----------
        resolution : list(int)
            Resolution in voxels of the world space (x, y, z)
        spacing : list(int)
            Length in millimeters of the voxels (sx, sy, sz)

        Returns
        -------
        GeometryHandler
            A geometry handler in which to put all the geometric primitives

        """
        return GeometryHandler(resolution, spacing)

    @staticmethod
    def create_cluster_meta(dimensions, fibers_per_bundle, sampling_distance, center, limits):
        """
        Creates a meta definition for a cluster. It represents the cluster space and contains the
        global parameters that will be applied to each of its underlying bundles.

        Parameters
        ----------
        dimensions : int
            Number of dimensions of the cluster's space
        fibers_per_bundle : int
           Number of fibers to generate in each bundle
        sampling_distance : float
            Distance to consider along the fibers between the anchors
        center : list(float)
            Center of the cluster in the cluster's space
        limits : list(list(int))
            Limits of the cluster's space along each dimension

        Returns
        -------
        ClusterMeta
            A cluster's meta definition

        """
        cluster_meta = ClusterMeta()
        cluster_meta.set_dimensions(dimensions)\
                    .set_center(center)\
                    .set_limits(limits)\
                    .set_density(fibers_per_bundle)\
                    .set_sampling(sampling_distance)

        return cluster_meta

    @staticmethod
    def create_cluster(meta, bundles=list, world_center=None):
        """
        Creates a cluster object

        Parameters
        ----------
         meta : ClusterMeta
            A cluster's meta definition
         bundles : list, optional
            A list of bundles composing the cluster, default : []
         world_center : list(float) or None, optional
            A center for the cluster's space in the world space. If None, will use the
            center defined in the meta definition, default : None

        Returns
        -------
        Cluster
            A cluster primitive

        """
        cluster = Cluster()
        cluster.set_cluster_meta(meta)\
               .set_bundles(bundles)\
               .set_world_center(world_center if world_center else meta.get_center())

        return cluster

    @staticmethod
    def create_bundle(radius, symmetry, n_point_per_centroid, anchors=list):
        """
        Creates a bundle object

        Parameters
        ----------
        radius : float
            Radius of the bundle
        symmetry : float
            A float, from -1 to 1, defining the elliptical shape of the bundle cross-section
        n_point_per_centroid : int
            Number of points sampling points along the spline representing the centroid
        anchors : list(list(int)) or list, optional
            List of anchor points defining the centroid of the bundle, default : []

        Returns
        -------
        Bundle
            A bundle primitive

        """
        bundle = Bundle()
        bundle.set_radius(radius)\
              .set_symmetry(symmetry)\
              .set_n_point_per_centroid(n_point_per_centroid)\
              .set_anchors(anchors)

        return bundle

    @staticmethod
    def rotate_bundle(bundle, center, angle, plane=Plane.XY, bbox=None, bbox_center=None):
        """
        Rotates a bundle (and its bounding box if supplied) of an angle along
        an axis perpendicular to a plane.

        Parameters
        ----------
        bundle : Bundle
            A bundle primitive
        center : list(float)
            Center to consider for the bundle (will be subtracted before rotation, then added)
        angle : float
            A rotation angle in radian
        plane : Plane, optional
            A plane against which the rotation will be done (see then Plane enum), default : Plane.XY
        bbox : list(list(float) or None, optional
            A bounding box around the bundle to transform as well, default : None
        bbox_center : list(float) or None, optional
            Center of the bounding box, default : None

        Returns
        -------
        list(list(float)) or None
            The transformed bounding box if supplied
        Bundle
            The transformed bundle

        """
        bbox, anchors = rotate_bundle(bundle, Rotation(plane).generate(angle), center, bbox, bbox_center)
        return bbox, GeometryFactory.create_bundle(
            bundle.get_radius(),
            bundle.get_symmetry(),
            bundle.get_n_point_per_centroid(),
            anchors
        )

    @staticmethod
    def translate_bundle(bundle, translation, bbox=None):
        """
        Translates a bundle (and its bounding box if supplied).

        Parameters
        ----------
        bundle : Bundle
            A bundle primitive
        translation : list(float)
            Translation vector
        bbox : list(list(float) or None, optional
            A bounding box around the bundle to transform as well, default : None

        Returns
        -------
        list(list(float)) or None
            The transformed bounding box if supplied
        Bundle
            The transformed bundle

        """
        bbox, anchors = translate_bundle(bundle, translation, bbox)
        return bbox, GeometryFactory.create_bundle(
            bundle.get_radius(),
            bundle.get_symmetry(),
            bundle.get_n_point_per_centroid(),
            anchors
        )

    @staticmethod
    def create_sphere(radius, center, scaling=1):
        """
        Creates a sphere object

        Parameters
        ----------
        radius : float
            Radius of the sphere
        center : list(float)
            Center of the sphere in the world
        scaling : float, optional
            A scaling value to apply to the sphere, default : 1

        Returns
        -------
        Sphere
            A sphere primitive

        """
        sphere = Sphere()
        sphere.set_radius(radius).set_center(center)
        if scaling > 0:
            sphere.set_scaling(scaling)

        return sphere

    @staticmethod
    def rotate_sphere(sphere, center, plane, angle):
        """
        Rotates a sphere of an angle along an axis perpendicular to a plane.

        Parameters
        ----------
        sphere : Sphere
            A bundle primitive
        center : list(float)
            Center to consider for the sphere (will be subtracted before rotation, then added)
        plane : Plane
            A plane against which the rotation will be done (see then Plane enum)
        angle : float
            A rotation angle in radian

        Returns
        -------
        Sphere
            The transformed sphere

        """
        new_sphere = Sphere()
        rotation = Rotation(plane).generate(angle)
        new_center = (rotation @ (array(sphere.get_center()) - center)) + center

        new_sphere.set_radius(sphere.get_radius())\
                  .set_center(new_center.tolist())\
                  .set_scaling(sphere.get_scaling())

        return new_sphere
