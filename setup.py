from setuptools import setup, find_packages

setup(
    name="interactive-estimation-system",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Backend dependencies
        "fastapi>=0.96.0",
        "uvicorn>=0.22.0",
        "pydantic>=2.0.0",
        "langchain>=0.0.267",
        "langchain-core>=0.1.0",
        "langchain-openai>=0.0.1",
        "langgraph>=0.0.10",
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
        
        # Frontend dependencies
        "streamlit>=1.23.0",
        "requests>=2.30.0",
    ],
    author="Shakil1819",
    author_email="shakilmrf8@gmail.com",
    description="An interactive estimation system using FastAPI, Langgraph, and Streamlit",
    keywords="estimation, langchain, streamlit, fastapi, langgraph",    python_requires=">=3.11",
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
        ],
        "dev": [
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "pre-commit>=3.3.3",
        ],
    },
)
