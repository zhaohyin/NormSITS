# NormSITS
A cross-platform Satellite Images Time Series(SITS) preprocessing system.

NormSITS is released under the terms of the MIT license, and thus free for commercial and research use. Feel free to normalized your own Satellite Images Time Series (SITS),to add NMAG in your own project.You are welcomed to make contributions to this project. Email zhyin@zju.edu.cn, or open an issue here on GitHub for support. 

Citation (more to be added soon):

    @article{Yin_2021,
    title={A Nonlinear Radiometric Normalization Model for Satellite Images Time Series Based on Artificial Neural Networks and Greedy Algorithm},
    author={Yin, Zhaohui; Sun, Jiayu; Zhang, Haoran; Zhang, Wenyi; Zou, Lejun.; Shen, Xiaohua},
    journal={Preprints 2021, 2021010609}
    year={2021}
    }

<img src='./png/Graphical_Abstract.jpg'>

## Dependencies
### GDAL

GDAL is a translator library for raster and vector geospatial data formats that is released under an X/MIT style Open Source [License](https://gdal.org/license.html#license) by the [Open Source Geospatial Foundation](https://www.osgeo.org/). As a library, it presents a single raster abstract data model and single vector abstract data model to the calling application for all supported formats. It also comes with a variety of useful command line utilities for data translation and processing. 

Version required: 2.3.3

### PyQt
PyQt is a set of Python bindings for The [Qt Company's](https://www.qt.io/) Qt application framework and runs on all platforms supported by Qt including Windows, macOS, Linux, iOS and Android.

Version required: 5.9.2

### MySQL
MySQL is the most popular relational database management system.

### NumPy
The fundamental package for scientific computing with Python.

Version: 1.16.5

## Functions
NormSITS provide a platform to handle the relative radiometric normalization of landsat-8 SITS.
In order to make users feel comfortable, NormSITS is designed to run in GUI mode. 

NormSITS include three main function:
1. Download Landsat-8 SITS、Landsat-7 SITS、Landsat-5 SITS.
2. Display each image in Landsat-8 SITS;
3. Clip landsat-8 SITS to obtain your own study area;
4. A nonlinear Radiometric Normalization Model for Satellite Imgaes Time Series (named NMAG) is implemented.

## Build from source
Suggestion: 
>[Anaconda](https://www.anaconda.com) is a distribution of the Python and R programming languages for scientific computing (data science, machine learning applications, large-scale data processing, predictive analytics, etc.), that aims to simplify package management and deployment. The distribution includes data-science packages suitable for Windows, Linux, and macOS. With the help of Anaconda, you can easily build up the environment.

First, all dependencies, python, GDAL, PyQt, Numpy, MySQL, Pandas, Matplotlib should be installed properly.

Then, Run this Command:

```zsh
(gdal-python) Star@zhyin NMAG_Experiment % python ui_designer.py
```

After a successful compilation, NormSITS looks like this:

<img src='./png/display.PNG'>