"""Educational source registry catalog and compliance manager."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.knowledge import EducationalSource
from app.core.logging import logger

# Official, verified educational sources with legal attribution and open/fair-dealing licensing
BUILTIN_EDUCATIONAL_SOURCES: List[Dict[str, Any]] = [
    # 1. NCERT Resources
    {
        "id": "ncert-math-class10",
        "source_name": "NCERT Class 10 Mathematics",
        "source_url": "https://ncert.nic.in/textbook.php?jemh1=0-15",
        "subject": "Mathematics",
        "academic_level": "Secondary (Grade 10)",
        "license_type": "NCERT Educational Fair Dealing (Indian Copyright Act Section 52(1)(a))",
        "source_authority": "National Council of Educational Research and Training (NCERT)",
        "authority_category": "ncert",
        "description": "Standard national curriculum covering Real Numbers, Polynomials, Linear Equations, Quadratic Equations, Triangles, Trigonometry, and Statistics.",
    },
    {
        "id": "ncert-physics-class11",
        "source_name": "NCERT Class 11 Physics (Part I & II)",
        "source_url": "https://ncert.nic.in/textbook.php?keph1=0-8",
        "subject": "Physics",
        "academic_level": "Higher Secondary (Grade 11)",
        "license_type": "NCERT Educational Fair Dealing",
        "source_authority": "National Council of Educational Research and Training (NCERT)",
        "authority_category": "ncert",
        "description": "Foundational physics covering Units and Measurement, Kinematics, Laws of Motion, Work, Energy & Power, Rotational Motion, Gravitation, and Thermodynamics.",
    },
    {
        "id": "ncert-chemistry-class12",
        "source_name": "NCERT Class 12 Chemistry",
        "source_url": "https://ncert.nic.in/textbook.php?lech1=0-9",
        "subject": "Chemistry",
        "academic_level": "Higher Secondary (Grade 12)",
        "license_type": "NCERT Educational Fair Dealing",
        "source_authority": "National Council of Educational Research and Training (NCERT)",
        "authority_category": "ncert",
        "description": "Senior chemistry covering Solutions, Electrochemistry, Chemical Kinetics, Coordination Compounds, Haloalkanes, and Biomolecules.",
    },

    # 2. Government Educational Portals
    {
        "id": "epathshala-portal",
        "source_name": "ePathshala National Educational Portal",
        "source_url": "https://epathshala.nic.in/",
        "subject": "STEM Curriculum",
        "academic_level": "K-12 (Grades 1-12)",
        "license_type": "Ministry of Education Govt of India Open Access",
        "source_authority": "Ministry of Education & CIET-NCERT, Government of India",
        "authority_category": "gov_portal",
        "description": "Joint initiative of Ministry of Education and NCERT disseminating educational e-resources, textbooks, audio, and video.",
    },
    {
        "id": "nptel-cs-foundations",
        "source_name": "NPTEL Computer Science & Discrete Mathematics",
        "source_url": "https://nptel.ac.in/courses/106106183",
        "subject": "Computer Science",
        "academic_level": "Undergraduate",
        "license_type": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)",
        "source_authority": "IIT Madras / Ministry of Education, Govt of India",
        "authority_category": "gov_portal",
        "description": "National Programme on Technology Enhanced Learning course materials for Algorithms, Discrete Mathematics, and Data Structures.",
    },

    # 3. Official University Materials
    {
        "id": "openstax-physics-vol1",
        "source_name": "OpenStax University Physics Volume 1",
        "source_url": "https://openstax.org/details/books/university-physics-volume-1",
        "subject": "Physics",
        "academic_level": "Undergraduate",
        "license_type": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "source_authority": "OpenStax / Rice University",
        "authority_category": "university",
        "description": "Peer-reviewed, openly licensed textbook covering Mechanics, Sound, Oscillations, and Waves for STEM majors.",
    },
    {
        "id": "openstax-calculus-vol1",
        "source_name": "OpenStax Calculus Volume 1",
        "source_url": "https://openstax.org/details/books/calculus-volume-1",
        "subject": "Mathematics",
        "academic_level": "Undergraduate",
        "license_type": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "source_authority": "OpenStax / Rice University",
        "authority_category": "university",
        "description": "Comprehensive calculus curriculum covering Functions, Limits, Derivatives, and Applications of Definite Integrals.",
    },
    {
        "id": "mit-ocw-6-0001",
        "source_name": "MIT OpenCourseWare: Intro to CS & Programming in Python",
        "source_url": "https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/",
        "subject": "Computer Science",
        "academic_level": "Undergraduate",
        "license_type": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)",
        "source_authority": "Massachusetts Institute of Technology (MIT)",
        "authority_category": "university",
        "description": "MIT introductory course syllabus, problem sets, and lecture notes on computation, algorithms, and Python programming.",
    },

    # 4. Open Educational Resources (OER)
    {
        "id": "libretexts-chem",
        "source_name": "LibreTexts Chemistry Open Educational Resource",
        "source_url": "https://chem.libretexts.org/",
        "subject": "Chemistry",
        "academic_level": "College & High School",
        "license_type": "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 (CC BY-NC-SA 3.0)",
        "source_authority": "LibreTexts Project / UC Davis",
        "authority_category": "oer",
        "description": "Community-driven open STEM textbook repository supported by the US Department of Education.",
    },
    {
        "id": "khan-academy-oer",
        "source_name": "Khan Academy STEM Learning Resources",
        "source_url": "https://www.khanacademy.org/",
        "subject": "Mathematics & Science",
        "academic_level": "K-12 & Early College",
        "license_type": "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 (CC BY-NC-SA 3.0)",
        "source_authority": "Khan Academy",
        "authority_category": "oer",
        "description": "Structured mastery-based conceptual explanations, worked examples, and exercises for Algebra, Geometry, and Biology.",
    },

    # 5. Official Programming Documentation
    {
        "id": "python-docs-312",
        "source_name": "Python 3.12 Official Documentation",
        "source_url": "https://docs.python.org/3/",
        "subject": "Computer Science",
        "academic_level": "All Levels",
        "license_type": "Python Software Foundation License Version 2 (PSF-2.0)",
        "source_authority": "Python Software Foundation (PSF)",
        "authority_category": "programming_docs",
        "description": "The definitive language reference, standard library manual, and tutorial for Python programming.",
    },
    {
        "id": "mdn-javascript",
        "source_name": "MDN Web Docs: JavaScript Guide & Reference",
        "source_url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
        "subject": "Computer Science",
        "academic_level": "All Levels",
        "license_type": "Creative Commons Attribution-ShareAlike 2.5 or later (CC-BY-SA 2.5+)",
        "source_authority": "Mozilla Developer Network (MDN)",
        "authority_category": "programming_docs",
        "description": "Comprehensive reference and tutorial documentation for modern ECMAScript / JavaScript.",
    },

    # 6. Academic Research Sources
    {
        "id": "arxiv-stem-archive",
        "source_name": "arXiv.org Open STEM Preprints",
        "source_url": "https://arxiv.org/",
        "subject": "STEM Research",
        "academic_level": "Advanced / Graduate",
        "license_type": "arXiv Non-exclusive Distribution License / Creative Commons",
        "source_authority": "Cornell University & arXiv Scientific Advisory Board",
        "authority_category": "research",
        "description": "Open access repository of electronic preprints covering Physics, Mathematics, Computer Science, and Quantitative Biology.",
    },
]


def seed_default_sources(db: Session) -> int:
    """Populate default verified educational sources in database if not already present."""
    count = 0
    now = datetime.utcnow()
    for item in BUILTIN_EDUCATIONAL_SOURCES:
        existing = db.query(EducationalSource).filter(EducationalSource.id == item["id"]).first()
        if not existing:
            source = EducationalSource(
                id=item["id"],
                source_name=item["source_name"],
                source_url=item["source_url"],
                subject=item["subject"],
                academic_level=item["academic_level"],
                license_type=item["license_type"],
                source_authority=item["source_authority"],
                authority_category=item["authority_category"],
                description=item.get("description"),
                collection_date=now,
                last_updated_date=now,
                is_active=True,
                document_count=0
            )
            db.add(source)
            count += 1
    if count > 0:
        db.commit()
        logger.info(f"Seeded {count} authoritative educational sources into registry.")
    return count


def validate_source_license_compliance(
    license_type: str,
    authority_category: str,
    source_url: str
) -> Dict[str, Any]:
    """Verify that a candidate educational source operates under legally compliant terms."""
    clean_lic = license_type.strip().lower()
    clean_cat = authority_category.strip().lower()

    compliant_license_keywords = [
        "creative commons", "cc by", "cc-by", "public domain",
        "fair dealing", "educational use", "open access",
        "psf", "mit", "apache", "bsd", "gnu", "open documentation"
    ]

    is_license_ok = any(kw in clean_lic for kw in compliant_license_keywords)
    is_url_ok = source_url.startswith("http://") or source_url.startswith("https://")
    is_category_ok = clean_cat in [
        "ncert", "gov_portal", "university", "oer", "programming_docs", "research"
    ]

    is_compliant = is_license_ok and is_url_ok and is_category_ok

    reasons = []
    if not is_url_ok:
        reasons.append("Invalid or missing canonical source URL.")
    if not is_category_ok:
        reasons.append(f"Authority category '{authority_category}' is not recognized.")
    if not is_license_ok:
        reasons.append(f"License '{license_type}' does not appear to be an acknowledged open educational or fair-dealing license.")

    return {
        "is_compliant": is_compliant,
        "reasons": reasons,
        "license_verified": is_license_ok,
    }

