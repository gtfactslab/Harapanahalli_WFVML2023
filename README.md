# WFVML Submission 22 Code

This is the accompanying code for the Workshop on Formal Verification of Machine Learning (WFVML) Submission 22, "A Toolbox for Fast Interval Arithmetic in `numpy` with an Application to Formal Verification of Neural Network Controlled Systems".

See [https://github.com/gtfactslab/npinterval](https://github.com/gtfactslab/npinterval) for the most up to date version of `npinterval`.

`npinterval` contains the toolbox introduced in Section 2 of the paper, and `ReachMM` contains code to implement Section 3 of the paper. To reproduce the figures from the paper, both `npinterval` and `ReachMM` are required.

## Create a new `conda` environment
```
conda create -n npinterval python=3.10
conda activate npinterval
```

## `npinterval` installation
Run the following
```
cd npinterval
pip install .
```
which will compile and install `npinterval` into the conda environment. Step back into the root folder.
```
cd ..
```

## `ReachMM` installation
```
cd ReachMM
```

Install `auto_LiRPA` (from [https://github.com/Verified-Intelligence/auto_LiRPA](https://github.com/Verified-Intelligence/auto_LiRPA)).
```
cd auto_LiRPA
python setup.py install
```
Step back into the `ReachMM` folder and install the `ReachMM` package and its dependencies.
```
cd ..
pip install -e .
```
## Reproducing Figures from the Submission

To reproduce Figure 1, run the following
```
python figure1.py
```
To reproduce Figure 2, run the following
```
python figure2.py -N 100
```
where `N` specifies the number of runs to average over.
