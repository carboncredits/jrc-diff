JRC-Diff
--------

A small script using [yirgacheffe](https://github.com/carboncredits/yirgacheffe) to calculate the difference between two [Tropial Moist Forest](https://forobs.jrc.ec.europa.eu/TMF) datasets.

The script will diff one file that should be in both the `--older` JRC dataset directory and the `--newer` dataset directory. You can then use some command-line parallelism to fan this out for as many JRC files as you like. For example, you could use [littlejohn](https://github.com/carboncredits/littlejohn) with a CSV file like:

```csv
--jrc-filename
JRC_TMF_AnnualChange_v1_2020_AFR_ID51_N10_W20.tif
...
```