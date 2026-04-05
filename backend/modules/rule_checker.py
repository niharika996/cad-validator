"""
Module 2: Rule Checker
Deterministic design rule checks — fast, 100% accurate, no AI needed.
These are hard engineering limits that are always true regardless of part type.
"""


def run_rule_checks(geometry: dict) -> list:
    """
    Run all rule checks against extracted geometry.
    Returns a list of violations, each with severity and fix suggestion.
    """
    violations = []

    violations += check_wall_thickness(geometry)
    violations += check_model_validity(geometry)
    violations += check_dimensions(geometry)
    violations += check_weight(geometry)
    violations += check_sharp_edges(geometry)
    violations += check_holes(geometry)
    violations += check_symmetry(geometry)
    violations += check_surface_area_ratio(geometry)

    return violations


# ── Individual Rule Functions ──

def check_wall_thickness(geo: dict) -> list:
    violations = []
    thickness = geo.get('min_wall_thickness_mm', 999)

    if thickness < 1.0:
        violations.append({
            'rule': 'Minimum Wall Thickness',
            'severity': 'CRITICAL',
            'detail': f'Minimum wall thickness is {thickness}mm. Absolute minimum for most manufacturing processes is 1.0mm.',
            'value': thickness,
            'threshold': 1.0,
            'fix': 'Increase wall thickness to at least 1.5mm. For injection molding, aim for 2.0-3.0mm.',
            'location': 'Thinnest wall section'
        })
    elif thickness < 1.5:
        violations.append({
            'rule': 'Recommended Wall Thickness',
            'severity': 'WARNING',
            'detail': f'Wall thickness of {thickness}mm is below the recommended 1.5mm minimum for reliable manufacturing.',
            'value': thickness,
            'threshold': 1.5,
            'fix': 'Increase wall thickness to 1.5mm or more for improved structural reliability.',
            'location': 'Thinnest wall section'
        })
    elif thickness < 2.0:
        violations.append({
            'rule': 'Wall Thickness Advisory',
            'severity': 'INFO',
            'detail': f'Wall thickness of {thickness}mm is acceptable but borderline. Consider increasing to 2mm for robustness.',
            'value': thickness,
            'threshold': 2.0,
            'fix': 'Optional: increase to 2mm for better structural margin.',
            'location': 'Thinnest wall section'
        })

    return violations


def check_model_validity(geo: dict) -> list:
    violations = []

    if not geo.get('is_watertight', True):
        violations.append({
            'rule': 'Model Integrity',
            'severity': 'CRITICAL',
            'detail': 'The model is not watertight — it has open gaps or holes in the mesh surface.',
            'value': 'Not watertight',
            'threshold': 'Watertight required',
            'fix': 'Close all open edges in your CAD model. Use the "Repair" or "Heal" function in your CAD tool.',
            'location': 'Mesh boundary edges'
        })

    return violations


def check_dimensions(geo: dict) -> list:
    violations = []
    l = geo.get('length_mm', 0)
    w = geo.get('width_mm', 0)
    h = geo.get('height_mm', 0)

    # Check for extremely flat parts (likely a modelling error)
    min_dim = min(l, w, h)
    max_dim = max(l, w, h)

    if min_dim < 0.5:
        violations.append({
            'rule': 'Minimum Feature Size',
            'severity': 'CRITICAL',
            'detail': f'One dimension is {min_dim}mm — extremely small and likely a modelling error or unit mismatch.',
            'value': min_dim,
            'threshold': 0.5,
            'fix': 'Check if your CAD units are set correctly (mm vs inches). Verify the model scale.',
            'location': 'Overall bounding box'
        })

    if max_dim > 2000:
        violations.append({
            'rule': 'Maximum Part Size',
            'severity': 'WARNING',
            'detail': f'Part dimension of {max_dim}mm exceeds 2000mm. Verify this is intentional and not a scale error.',
            'value': max_dim,
            'threshold': 2000,
            'fix': 'Confirm units are in mm and the part size is intentional.',
            'location': 'Overall bounding box'
        })

    return violations


def check_weight(geo: dict) -> list:
    violations = []
    weight = geo.get('estimated_weight_g', 0)

    if weight > 50000:
        violations.append({
            'rule': 'Part Weight',
            'severity': 'WARNING',
            'detail': f'Estimated weight is {weight}g ({weight/1000:.1f}kg). This is very heavy — verify material and geometry.',
            'value': weight,
            'threshold': 50000,
            'fix': 'Consider lightweighting — add pockets, ribs, or switch to a lighter material.',
            'location': 'Entire part volume'
        })
    elif weight > 10000:
        violations.append({
            'rule': 'Part Weight Advisory',
            'severity': 'INFO',
            'detail': f'Estimated weight is {weight}g ({weight/1000:.1f}kg). Consider if this meets assembly and handling requirements.',
            'value': weight,
            'threshold': 10000,
            'fix': 'Review if weight reduction is needed for your application.',
            'location': 'Entire part volume'
        })

    return violations


def check_sharp_edges(geo: dict) -> list:
    violations = []
    sharp = geo.get('sharp_edge_count', 0)
    faces = geo.get('face_count', 1)

    # Sharp edges as a proportion of total faces
    ratio = sharp / faces if faces > 0 else 0

    if ratio > 0.3:
        violations.append({
            'rule': 'Sharp Edge Density',
            'severity': 'WARNING',
            'detail': f'{sharp} sharp edges detected ({ratio*100:.0f}% of faces). Sharp corners cause stress concentration and manufacturing issues.',
            'value': sharp,
            'threshold': int(faces * 0.3),
            'fix': 'Add fillets (rounded corners) of at least 0.5mm radius to all sharp internal edges.',
            'location': 'Multiple edge locations'
        })
    elif ratio > 0.15:
        violations.append({
            'rule': 'Sharp Edge Advisory',
            'severity': 'INFO',
            'detail': f'{sharp} sharp edges found. Consider adding fillets to improve durability.',
            'value': sharp,
            'threshold': int(faces * 0.15),
            'fix': 'Add 0.5mm minimum fillet radius to sharp edges.',
            'location': 'Multiple edge locations'
        })

    return violations


def check_holes(geo: dict) -> list:
    violations = []
    holes = geo.get('holes', [])

    for hole in holes:
        diameter = hole.get('diameter_mm', 0)
        if diameter < 1.0:
            violations.append({
                'rule': 'Minimum Hole Diameter',
                'severity': 'CRITICAL',
                'detail': f'Hole diameter of {diameter}mm is too small for standard manufacturing. Minimum drillable hole is 1.0mm.',
                'value': diameter,
                'threshold': 1.0,
                'fix': 'Increase hole diameter to at least 1.0mm, or use EDM for smaller features.',
                'location': f'Hole at position {hole.get("center", "unknown")}'
            })
        elif diameter < 2.0:
            violations.append({
                'rule': 'Small Hole Warning',
                'severity': 'WARNING',
                'detail': f'Hole diameter of {diameter}mm is very small and may be difficult to manufacture reliably.',
                'value': diameter,
                'threshold': 2.0,
                'fix': 'Consider increasing to 2.0mm for standard drilling. Confirm with manufacturing team.',
                'location': f'Hole at position {hole.get("center", "unknown")}'
            })

    return violations


def check_symmetry(geo: dict) -> list:
    violations = []

    # Only flag asymmetry if the part appears structural (high aspect ratio)
    aspect = geo.get('aspect_ratio_lw', 1)
    is_symmetric = geo.get('is_symmetric', True)

    if not is_symmetric and 0.8 < aspect < 1.2:
        # Square-ish part that isn't symmetric — likely a bracket or plate
        violations.append({
            'rule': 'Geometric Symmetry',
            'severity': 'INFO',
            'detail': 'Part appears asymmetric. If this is a structural or load-bearing component, asymmetry can cause uneven stress distribution.',
            'value': 'Asymmetric',
            'threshold': 'Symmetric recommended',
            'fix': 'Review load paths and verify asymmetry is intentional. Add symmetric features if needed.',
            'location': 'Overall part geometry'
        })

    return violations


def check_surface_area_ratio(geo: dict) -> list:
    violations = []
    volume = geo.get('volume_mm3', 1)
    area = geo.get('surface_area_mm2', 1)

    if volume <= 0:
        return violations

    # Surface area to volume ratio — very high ratio may indicate paper-thin geometry
    ratio = area / volume
    if ratio > 10:
        violations.append({
            'rule': 'Surface-to-Volume Ratio',
            'severity': 'INFO',
            'detail': f'High surface-to-volume ratio ({ratio:.1f}). Part may be very thin or have complex surface geometry — verify manufacturability.',
            'value': round(ratio, 2),
            'threshold': 10,
            'fix': 'Review thin sections and complex surfaces for manufacturing feasibility.',
            'location': 'Overall part geometry'
        })

    return violations
