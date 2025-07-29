# How Researchers Claim Novelty in Biomedical Science: A Taxonomy for Understanding Innovation

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

NovelTax is a comprehensive framework for detecting and classifying novelty mentions in biomedical literature using advanced natural language processing techniques. The system leverages OpenAI's GPT models to analyze PubMed abstracts and classify sentences based on their novelty characteristics.

## Features

- **Automated Novelty Detection**: Identifies novelty mentions in biomedical abstracts using keyword-based detection
- **AI-Powered Classification**: Utilizes OpenAI GPT models for sophisticated novelty classification
- **Batch Processing**: Efficient batch processing capabilities for large-scale analysis
- **Flexible Taxonomy**: Customizable taxonomy system for novelty classification
- **Comprehensive Logging**: Detailed logging and timing information for research reproducibility

## Web-Based Annotation Platform

https://clinicalnlp.org/novelty-reviewer/

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/NovelTax.git
cd NovelTax
```

2. Install required dependencies:
```bash
pip install -r req.txt
```

3. Set up environment variables:
```bash
cp dotenv.tpl .env
# Edit .env and add your OpenAI API key
```

**Note**: The complete configuration files in the `novelty_reviewer/` directory will be released upon publication.

## Usage

### Basic Workflow

1. **Prepare Input Data**: Ensure your input TSV file contains the following columns:
   - `pmid`: PubMed ID
   - `conclusions`: Abstract conclusions or text to analyze

2. **Configure Settings**: 
   - The `novelty_reviewer/` directory contains configuration files that will be released upon publication
   - Place your prompt template and taxonomy files in the `novelty_reviewer/` directory

3. **Run Novelty Detection**:
```python
from annotation_preparation import main
main()
```

4. **Process with OpenAI Batch API**:
```python
from nb_openai_batch import main
main()
```

### Configuration

#### Input File Format
Your input TSV file should have the following structure:
```
pmid    conclusions
12345   This study presents a novel approach to...
67890   We developed an innovative method for...
```

#### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)

## Project Structure

```
NovelTax/
├── README.md                 # This file
├── LICENSE                   # Apache 2.0 License
├── req.txt                   # Python dependencies
├── dotenv.tpl               # Environment template
├── .gitignore               # Git ignore rules
├── functions.py             # Utility functions
├── annotation_preparation.py # Novelty detection pipeline
├── nb_openai_batch.py       # OpenAI batch processing
└── novelty_reviewer/        # Configuration directory (to be released upon publication)
```

## API Reference

### Core Functions

#### `novelty_detection(df, section, keywords, logger=None)`
Detects novelty mentions in text using keyword matching.

**Parameters:**
- `df`: DataFrame containing the data
- `section`: Column name containing text to analyze
- `keywords`: List of novelty keywords to search for
- `logger`: Optional logger instance

#### `convert_tsv_to_jsonl(tsv_fp, jsonl_fp, taxonomy, model, _prompt)`
Converts TSV input to JSONL format for OpenAI batch processing.

#### `upload_jsonl(jsonl_fp, headers)`
Uploads JSONL file to OpenAI for batch processing.

## Contributing

We welcome contributions! Please see our contributing guidelines for details.

## Citation

If you use NovelTax in your research, please cite our paper:

```bibtex
@article{noveltax2024,
  title={How Researchers Claim Novelty in Biomedical Science: A Taxonomy for Understanding Innovation},
  author={TBD},
  journal={TBD},
  year={2024}
}
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for providing the GPT models
- PubMed for biomedical literature access
- The research community for feedback and contributions

## Contact

For questions and support, please open an issue on GitHub or contact the maintainers.

---

**Note**: The full dataset and complete codebase, including the web-based annotation platform, will be released publicly upon publication. 