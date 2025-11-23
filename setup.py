from setuptools import setup, find_packages

setup(
    name="scraping-refactor",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "aiohttp>=3.8.0,<4.0.0",
        "beautifulsoup4>=4.14.0,<5.0.0", 
        "playwright>=1.56.0,<2.0.0",
        "SQLAlchemy>=2.0.0,<3.0.0",
        "pytest>=7.0.0,<8.0.0",
        "pytest-asyncio>=0.21.0,<1.0.0",
    ],
    extras_require={
        "dev": [
            "radon>=6.0.0",
            "bandit>=1.7.0", 
            "safety>=3.0.0",
            "pytest-cov>=4.0.0",
        ]
    }
)
