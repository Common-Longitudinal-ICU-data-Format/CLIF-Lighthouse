# CLIF-Lighthouse

## Setup Instructions

### :warning: Deactivate Any Currently Active Environment(s) :warning:

Before proceeding, deactivate any existing virtual environment:

```sh
deactivate
```
#### and/or
```sh
conda deactivate
```

## A. Environment setup

The environment setup code is provided in the setup.sh file for macOS and setup.bat for Windows.

### For macOS:

#### 1. Make the `setup.sh` script executable
In the command line, navigate to the directory where the setup.sh file is located and run:
```sh
chmod +x setup.sh
```

#### 2. Run the script
```sh
./setup.sh
```

### For Windows:

Run the script
```sh
setup.bat
```

## B. Application Launch
To start the application navigate to the app directory in the terminal by executing the following command:

```
cd app
streamlit run app.py
```



