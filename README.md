# Montreal Forced Aligner (MFA) Pipeline
Pipeline for using the Montreal Forced Aligner (MFA) to automatically annotate speech task data.

This code utilizes functionality from the [Montreal Forced Aligner](https://montreal-forced-aligner.readthedocs.io/en/latest/index.html) to automatically mark word and phoneme level timings of patient responses for Cogan Lab speech tasks. See instructions below on how to install and use the pipeline.

**Currently supported tasks: Phoneme Sequencing, Sentence Repetition, Lexical Repeat, Picture Naming**

## Installation
1. Clone this repository to your preferred location on your computer.
2. Create a Python environment containing the packages defined in the `environment.yml` ([Anaconda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file)) or `requirements.txt` ([pip](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)) files contained in this repository.
3. Activate your newly created MFA Python Environment in a terminal window.
4. Download the proper acoustic models and dictionaries from the MFA. This is done with the following commands:
    - Pretrained acoustic model: `mfa model download acoustic english_us_arpa`
    - Word-to-phoneme dictionary: `mfa model download dictionary english_us_arpa`\
This will place the acoustic model and dictionary in subfolders in the `Documents/MFA/pretrained_models/` directory.
5. Copy the additional dictionary files from `dictionary/` in this repository to `Documents/MFA/pretrained_models/dictionary/`. Some of the tasks include non-words that are not included in the previoulsy downloaded dictionary, so we need to put these custom dictionaries containing the non-words in the same place as the other dictionary. No custom acoustic models are necessary.

## Usage
This pipeline assumes you have a directory of patients' speech task data with the following file structure (other files may be present, but these files are required):
```
<path_to_patients>/
    patient1/
        allblocks.wav
        cue_events.txt
        trialInfo.mat
    patient2/
        allblocks.wav
        cue_events.txt
        trialInfo.mat
    ...
```
The `MFA_pipeline.py` code will use these files to automatically transcribe and mark patient responses. 

Parameters to run the pipeline are contained in the `config.yaml` file. The following parameters can be modified:
- `patient_dir`: Path to the directory containing patient data (<path_to_patients> in the example above). **This is a required parameter.**
- `task`: The speech task that the patients are performing. Defaults to 'phoneme_sequencing'. Implemented tasks are contained in the `conf/task/` directory. The specified task must be an implemented task.
- `patients`: IDs of the patients to run the MFA on in the directory specified above, or 'all' to run on all patients. Defaults to 'all'.
- `patient_prefixes`: Prefixes of the patient IDs to auto-detect patients if `patients` is set to 'all'. Defaults to 'D*, S*', where * is a wildcard to allow for any characters after the prefix.
- `merge_thresh`: Thresold for merging adjacent words into a single utterance during MFA proeceessing. Defaults to 0.5 seconds.
- `only_stims`: Whether annotate only stimuli (True) or both responses and stimuli (False). Defaults to False.
- `debug_mode`: Whether to run the pipeline in debug mode (True), where errors encountered interrupt the processing, or in normal mode (False), where errors are gracefully handled and processing continues. Defaults to False.

Additional parameters are included for specific tasks contained in the `conf/task/` directory. These parameters are as follows:

- `name`: Task name.
- `stim_dir`: Directory containing stimuli for the task.
- `max_dur`: Max duration of responses in seconds.
- `mfa`: Settings for running the MFA specifying the dictionary and acoustic model to use.
- `cue_text`: Dictionary mapping cue event labels to speech content (e.g. _dog_ -> _The dog was very proud of the bell._)

### To run the pipeline:

1. Open a terminal window and activate your newly created MFA Python environment.
2. Make sure that you have downloaded the proper acoustic models and dictionaries defined in steps 4-5 of the **Installation** section.
3. Navigate to the directory where you cloned this repository.
4. Run the following command in the terminal:
```
python mfa_pipeline.py patient_dir=<path_to_patients>
```
where `<path_to_patients>` is the path to the directory containing patient data.

Parameters will be set to their default values as described above and in the `config.yaml` file. These parameters can be overridden in the command line when running the pipeline. For example:
```
python mfa_pipeline.py patient_dir=<path_to_patients> task=sentence_repetition patients=D101 only_stims=True debug_mode=True
```

Within each patient's directory, outputs from this pipeline will be contained in a new `mfa` directory. Relevant outputs include:
- `mfa_stim_words.txt`: Word-level timings of task stimuli.
- `mfa_stim_phones.txt`: Phoneme-level timings of task stimuli.
- `mfa_resp_words.txt`: Word-level timings of patient responses.
- `mfa_resp_phones.txt`: Phoneme-level timings of patient responses.
- `annotated_resp_windows.txt`: Windows of patient responses that are input to the MFA. This can be used for debugging if the MFA-annotated responses are not as expected to make sure that the MFA is receiving the correct windows to annotate.

*For lexical delay patients, additional tiers will be included for patients' "yes" and "no" responses. Since these trials can have variable responses ("yes" or "no" for each trial), one MFA instance generates a transcript by assuming the answer is always yes (outputs to the label files `mfa_yes_(words/phones).txt`) and another assumes the answer is always no (`mfa_no_(words/phones).txt`). As above, windows fed into the MFA are available in `annotated_(yes/no)_windows.txt`. Upon manual review of the MFA labels (see below), the incorrect assumed responses can be deleted (**right-click and choose "Delete Label" in Audacity. Pressing "Del" on the highlighted label will remove that SECTION OF TIME, causing all following annotations to be SHIFTED OUT OF ALIGNMENT**).

`input_mfa/` and `output_mfa/` directories will also be created in the patient's directory. These directories contain the input files for running the MFA and the unprocessed MFA outputs. These are only handled by the pipeline and should not be necessary for use.

### Using generated txt files
MFA-annotations described above (`mfa_stim_words.txt`, `mfa_stim_phones.txt`, `mfa_resp_words.txt`, `mfa_resp_phones.txt`) can be loaded into Audacity to visualize the annotations alongside the patient's audio file. To do this, first load `allblocks.wav` into Audacity. Then, import the desired `.txt` files as labels by going to 'File->Import->Labels' and selecting the `.txt` file.

MFA annotations likely contain minor timing errors, so manual correction of the labels can be done by dragging label boundaries to the correct location after loading into Audacity. **If you do this, make sure to save the modified labels under a new name so they don't get overwritten if you run the MFA on this patient again!**
