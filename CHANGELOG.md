# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-04-25

### Added
- Initial project structure for Interactive Estimation System
- FastAPI backend with conversational flow using Langgraph
- Streamlit frontend with chat interface and image upload
- Estimation logic for calculating quotes based on user input
- In-memory session management
- Configuration system for service parameters
- Test suite using pytest
- Docker and Docker Compose support
- GitHub Actions CI workflow
- Documentation including README, INSTALL, USER_GUIDE, and ARCHITECTURE docs

### Changed
- N/A (Initial release)

### Fixed
- Fixed recursion limit error in graph.py by changing `estimation_graph.invoke()` to `estimation_graph.ainvoke()` with a higher recursion limit
- Fixed infinite recursion loop by modifying the graph to end after generating a response
- Fixed AttributeError with Langgraph results by properly converting AddableValuesDict to GraphState objects
- Added warning filters to suppress PydanticSchemaJson warnings
- Fixed issue where system kept repeating "I have all the information I need" by preserving previous state and adding contextual follow-up responses
- Improved state handling and preservation between graph executions
