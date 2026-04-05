"""
Module 1: Geometry Extractor
Reads STL/OBJ files and extracts all measurable geometric properties.
This is the foundation — everything else depends on what this returns.
"""

import trimesh
import numpy as np
import os


def extract_geometry(filepath: str) -> dict:
    """
    Load a 3D model and extract geometry data.
    Returns a clean dictionary that all other modules consume.
    """
    ext = os.path.splitext(filepath)[1].lower()

    mesh = trimesh.load(filepath, force='mesh')

    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Could not load file as a valid 3D mesh.")

    # ── Basic dimensions ──
    bounds = mesh.bounds  # [[minX,minY,minZ],[maxX,maxY,maxZ]]
    size = bounds[1] - bounds[0]  # [length, width, height]

    # ── Wall thickness estimation ──
    # Sample rays through the mesh to estimate minimum wall thickness
    min_thickness = estimate_min_wall_thickness(mesh)

    # ── Holes detection ──
    holes = detect_holes(mesh)

    # ── Sharp edges ──
    sharp_edges = detect_sharp_edges(mesh)

    # ── Symmetry check ──
    is_symmetric = check_symmetry(mesh)

    # ── Surface quality ──
    is_watertight = mesh.is_watertight  # No gaps in the model

    geometry = {
        # Dimensions in mm (assumes STL units are mm)
        'length_mm': round(float(size[0]), 2),
        'width_mm': round(float(size[1]), 2),
        'height_mm': round(float(size[2]), 2),

        # Volume and area
        'volume_mm3': round(float(mesh.volume), 2),
        'surface_area_mm2': round(float(mesh.area), 2),

        # Estimated weight (assuming steel: 7.85 g/cm3)
        'estimated_weight_g': round(float(mesh.volume / 1000) * 7.85, 2),

        # Wall thickness
        'min_wall_thickness_mm': round(float(min_thickness), 2),

        # Holes
        'hole_count': len(holes),
        'holes': holes,

        # Sharp edges (potential stress points)
        'sharp_edge_count': sharp_edges,

        # Model health
        'is_watertight': bool(is_watertight),
        'is_symmetric': is_symmetric,
        'face_count': len(mesh.faces),
        'vertex_count': len(mesh.vertices),

        # Bounding box aspect ratio — helps AI identify part type
        'aspect_ratio_lw': round(float(size[0] / size[1]) if size[1] > 0 else 0, 2),
        'aspect_ratio_lh': round(float(size[0] / size[2]) if size[2] > 0 else 0, 2),
    }

    return geometry


def estimate_min_wall_thickness(mesh: trimesh.Trimesh) -> float:
    """
    Estimates minimum wall thickness by casting rays through the mesh
    and measuring the distance between entry and exit points.
    """
    try:
        # Sample points on the surface
        sample_count = 200
        points, face_indices = trimesh.sample.sample_surface(mesh, sample_count)
        normals = mesh.face_normals[face_indices]

        thicknesses = []
        for point, normal in zip(points, normals):
            # Cast ray inward
            ray_origin = point + normal * 0.01  # offset slightly
            ray_direction = -normal

            locations, _, _ = mesh.ray.intersects_location(
                ray_origins=[ray_origin],
                ray_directions=[ray_direction]
            )
            if len(locations) > 0:
                dist = np.linalg.norm(locations[0] - point)
                if 0.1 < dist < 100:  # Reasonable thickness range
                    thicknesses.append(dist)

        if thicknesses:
            return min(thicknesses)
        else:
            # Fallback: use smallest bounding box dimension / 4
            bounds = mesh.bounds
            size = bounds[1] - bounds[0]
            return float(min(size)) / 4

    except Exception:
        bounds = mesh.bounds
        size = bounds[1] - bounds[0]
        return float(min(size)) / 4


def detect_holes(mesh: trimesh.Trimesh) -> list:
    """
    Detects circular holes in the mesh by finding boundary loops
    that form approximate circles.
    """
    holes = []
    try:
        # Get mesh outline (boundary edges)
        outline = mesh.outline()
        if outline and hasattr(outline, 'entities'):
            for entity in outline.entities:
                vertices = outline.vertices[entity.points]
                if len(vertices) >= 6:  # Minimum points for a circle
                    # Fit a circle to these points
                    center, radius = fit_circle_to_points(vertices)
                    if radius and 0.5 < radius < 50:  # Reasonable hole sizes
                        holes.append({
                            'diameter_mm': round(float(radius * 2), 2),
                            'center': [round(float(c), 2) for c in center[:2]]
                        })
    except Exception:
        pass

    return holes


def fit_circle_to_points(points: np.ndarray):
    """Simple circle fitting using centroid and mean radius."""
    try:
        pts_2d = points[:, :2]
        center = pts_2d.mean(axis=0)
        radii = np.linalg.norm(pts_2d - center, axis=1)
        radius = radii.mean()
        variance = radii.std()
        # Only return if points are actually circular (low variance)
        if variance / radius < 0.2:
            return center, radius
    except Exception:
        pass
    return None, None


def detect_sharp_edges(mesh: trimesh.Trimesh) -> int:
    """
    Counts edges where the angle between adjacent faces is very sharp.
    Sharp edges (< 30 degrees) are stress concentration points.
    """
    try:
        # Face adjacency angles
        angles = trimesh.graph.face_adjacency_angles(mesh)
        # Count edges sharper than 30 degrees (0.52 radians)
        sharp_count = int(np.sum(angles < 0.52))
        return sharp_count
    except Exception:
        return 0


def check_symmetry(mesh: trimesh.Trimesh) -> bool:
    """
    Checks if the mesh is roughly symmetric about its center plane.
    """
    try:
        center = mesh.centroid
        vertices = mesh.vertices
        # Check X-axis symmetry
        left = vertices[vertices[:, 0] < center[0]]
        right = vertices[vertices[:, 0] > center[0]]
        if len(left) == 0 or len(right) == 0:
            return False
        ratio = min(len(left), len(right)) / max(len(left), len(right))
        return ratio > 0.75
    except Exception:
        return False
