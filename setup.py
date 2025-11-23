from setuptools import setup, find_packages

setup(
    name="trpg-llm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "litellm>=1.20.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.26.0",
        "aiofiles>=23.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
        ]
    },
    python_requires=">=3.9",
    author="TRPG-LLM Team",
    description="A configuration-driven TRPG framework with LLM integration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
