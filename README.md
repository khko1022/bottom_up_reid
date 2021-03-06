# Unsupervised Person Re-identification for Person Search
This repository is for UNIST lecture "Machin learning fundamentals" final project. The code is based on the [A Bottom-Up Clustering Approach to Unsupervised Person Re-identification](https://github.com/vana77/Bottom-up-Clustering-Person-Re-identification) library. 
<!-- 
## Performances
The performances is listed below:

|       | mAP     |rank-1     | rank-5     | rank-10     | 
| ---------- | :-----------:  | :-----------: |:-----------:  | :-----------: |
| PRW     |  19.1%| 47.3%| 59.2% | 63.7% |
| PRW with constraint    | 19.4% | 49.4%|59.6%| 64.9%| -->

## Preparation
### Dependencies
You can easily set the environment with docker. You can download docker images khko/pytorch:1.4.0 on docker hub.

- Python 3.6
- PyTorch (version >= 0.4.1)
- h5py, scikit-learn, metric-learn, tqdm

### Download datasets 
- PRW: You can download datasets [here](https://drive.google.com/file/d/13-rHAm120Rqhx7oaIB6GJIUB_WiYjK8W/view?usp=sharing) and set the datasets path on run.py.

## Usage
You can set following 4 experiments on run.sh.
- bucc: bottom_up_clustering_constraint
- burn: bottom_up_real_negative
- mst: ms_table
- msrn: ms_real_negative

You can set following suboptions.
- step size(init step/later step): reid/bottom_up.py initial_steps and step_size
- margin: reid/exclusive_loss.py: self.p_margin, self.n_margin

### Training
1. set dataset path on the run.py args.data_dir
2. choose combination of 4 options(bucc, burn, mst, msrn) on the run.sh
3. training:
```shell
sh ./run.sh
```

