# World phonotactics database

[![Build Status](https://travis-ci.org/cldf-datasets/phonotactics.svg?branch=master)](https://travis-ci.org/cldf-datasets/phonotactics)

Cite the source dataset as

> Donohue, Mark, Rebecca Hetherington, James McElvenny and Virginia Dawson. 2013. World phonotactics database. Department of Linguistics, The Australian National University. 

This dataset is licensed under a CC-BY-4.0 license

Available online at https://doi.org/10.5281/zenodo.815506


The data in this repository used to be available online, with a browsable web
interface at http://phonotactics.anu.edu.au/
At this point in time (2020-01-17) it has disappeared.

Luckily, the data has survived in the form of a CSV dump archived on Zenodo:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.815506.svg)](https://doi.org/10.5281/zenodo.815506)

Thus, the [CLDF](https://cldf.clld.org) dataset curated in this repository is derived
from the data dump on Zenodo.

The dataset provides data on more than 3,500 languages, including a rich set of
[language metadata](cldf/languages.csv). The [184 language features](cldf/parameters.csv) for which this dataset provides [values](cldf/values.csv) are grouped
in three datatypes (as specified in the `datatype` column):
```shell script
  "datatype"

	Type of data:          Text
	Contains null values:  False
	Unique values:         3
	Longest value:         7 characters
	Most common values:    boolean (144x)
	                       integer (36x)
	                       number (3x)

```
Numeric data (datatype `integer` and `number`) comes with a specification of minimum and
maximum reported values in the `cldf/parameters.csv`.
