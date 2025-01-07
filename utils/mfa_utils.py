import os
import subprocess
from pathlib import Path
import shutil
import glob
from typing import Optional, Union
from textgrid import TextGrid, IntervalTier
import numpy as np
import scipy.io as sio


def makeMFADirs(base_path: str):
    """Create directories for Montreal Forced Aligner (MFA).
    
    Creates an 'mfa' directory in the specified base directory, with
    'input_mfa' and 'output_mfa' subdirectories.

    Args:
        base_path (str): Path to the directory where mfa directories will be
        created.
    """    
    base_path = Path(base_path)
    mfa_dir = base_path / 'mfa'
    input_mfa_dir = mfa_dir / 'input_mfa'
    output_mfa_dir = mfa_dir / 'output_mfa'
    os.makedirs(mfa_dir, exist_ok=True)
    os.makedirs(input_mfa_dir, exist_ok=True)
    os.makedirs(output_mfa_dir, exist_ok=True)


def calculateAudDur(wav_path: str) -> float:
    """Calculate the duration of an audio file in seconds.

    Args:
        wav_path (str): Path to the audio file (assumed to be a .wav file).

    Returns:
        float: Duration of the audio file in seconds.

    """
    a = sio.wavfile.read(wav_path)
    fs = a[0]
    time = (np.array(a[1],dtype=float)).shape[0] / fs
    return time

def txt2textGrid(txt_path: str, tg_name: str, tg_dir: Optional[str] = None,
                 tier_name: str = 'words', return_tg: bool = False) \
        -> Optional[TextGrid]:
    """Converts a text file with format:
    start_time    end_time    label
    to a TextGrid object and saves it to a .TextGrid file.

    Args:
        txt_path (str): Path to txt file.
        tg_name (str): Name of the new TextGrid file.
        tg_path (Optional[str], optional): Path to save new TextGrid file. If
            None, the TextGrid file will be saved in the same directory as the
            txt file. Defaults to None.
        tier_name (str, optional): Label for the interval tier of the
            TextGrid file containing annotations. Defaults to 'words'.
        return_tg (bool, optional): Flag to return the created TextGrid object.
            Defaults to False.

    Returns:
        Optional[TextGrid]: TextGrid object if return_tg is True.
    """

    # save tg file in the same directory as txt file if not direectory is
    # specified
    if tg_dir is None:
        tg_dir = Path(txt_path).parent
        # tg_path = os.path.join(os.path.dirname(txt_path), tg_name +
        #                        '.TextGrid')
    tg_path = tg_dir / tg_name

    # Load your text file
    entries = []
    with open(txt_path, 'r') as f:
        for line in f:
            line_split = line.strip().split('\t')
            # skip lines with no labels
            if len(line_split) == 2:
                continue
            start, end, label = line_split
            entries.append((float(start), float(end), label))

    # Create a TextGrid object and add an interval tier
    tg = TextGrid()
    tier = IntervalTier(name=tier_name)

    # Add intervals from your text file to the tier
    for start, end, label in entries:
        tier.add(start, end, label)

    # Add the tier to the TextGrid
    tg.append(tier)

    # Save the TextGrid
    tg.write(tg_path)

    if return_tg:
        return tg
    

def textGrid2txt(tg_path: str, txt_name: str, txt_dir: Optional[str] = None,
                 tier_name: Union[str, list[str]] = ['words', 'phones'])-> None:
        """Converts a TextGrid file to a txt file with format:
        start_time    end_time    label
        A separate text file is created for each tier in the TextGrid file.
    
        Args:
            tg_path (str): Path to TextGrid file.
            txt_name (str): Name of the new txt file. If multiple tiers are
                extracted from the textGrid files, multiple txt files will be
                created in the format '{txt_name}_{tier_name}.txt'.
            txt_path (Optional[str], optional): Path to save new txt file. If
                None, the txt file will be saved in the same directory as the
                TextGrid file. Defaults to None.
            interval_label (str | list[str], optional): Label for the interval
            tier of the TextGrid file containing annotations.
            Defaults to ['words', 'phones'].
        """
    
        # save txt file in the same directory as tg file if not direectory is
        # specified
        if txt_dir is None:
            txt_dir = Path(tg_path).parent
            # txt_path = os.path.join(os.path.dirname(tg_path), txt_name +
            #                         '.txt')
        txt_path = txt_dir / txt_name
        
        # Ensure tier_name is a list for iteration
        if not isinstance(tier_name, list):
            tier_name = [tier_name]
    
        # Load the TextGrid file
        tg = TextGrid.fromFile(tg_path)
    
        for tier in tier_name:
            if tier not in tg.getNames():
                raise ValueError(f'Tier "{tier}" not found in TextGrid file.')
            curr_tier = tg.getFirst(tier)

            # write times and labels to txt file
            with open(txt_path.as_posix() + '_' + tier + '.txt', 'w',
                      encoding='utf-8') as f:
                for interval in curr_tier:
                    start = interval.minTime
                    end = interval.maxTime
                    label = interval.mark
                    if not label:  # remove empty labels btw words
                        continue
                    f.write(f'{start}\t{end}\t{label}\n')


def prepareForMFA(base_dir: str, wav_path: Optional[str] = None,
                  tg_path: Optional[str] = None,
                  wav_name_out: Optional[str] = None,
                  tg_name_out: Optional[str] = None,
                  input_dir_name: str = 'input_mfa',
                  output_dir_name: str = 'output_mfa') -> None:
    """Prepare files for Montreal Forced Aligner (MFA) by moving audio and
    transcript files to a newly created MFA input directory. An output
    directory is also created to store MFA output files.

    Args:
        base_dir (str): Path to the directory where input and output mfa
            directories will be created.
        wav_path (str, optional): Path to the audio file being used for the
            MFA. If unspecified, the function assumes the audio file is titled
            'allblocks.wav' and is located in the base directory.
            Defaults to None.
        tg_path (str, optional): Path to the transcript file being used for the
            MFA. If unspecified, the function assumes the audio file is titled
            'allblocks.TextGrid' and is located in the base directory.
            Defaults to None.
        wav_name_out (str, optional): Name for the audio file in the MFA input
            directory. Gives the option to rename the audio file.
            Defaults toNone.
        tg_name_out (str, optional): Name for the transcript file in the MFA
            input directory. Gives the option to rename the transcript file.
            Defaults to None.
    """    
    base_path = Path(base_dir)
    
    # assume allblocks.wav and allblocks.TextGrid are in the base directory if
    # no paths are provided
    if wav_path is None:
        wav_path = base_path / 'allblocks.wav'
    else:
        wav_path = Path(wav_path)

    if tg_path is None:
        tg_path = base_path / 'allblocks.TextGrid'
    else:
        tg_path = Path(tg_path)

    # MFA input and output folders to run from command line
    input_mfa_dir = base_path / input_dir_name
    # output_mfa_dir = base_path / output_dir_name
    # os.makedirs(input_mfa_dir, exist_ok=True)
    # os.makedirs(output_mfa_dir, exist_ok=True)

    # move wav (audio) and TextGrid (transcript) to input directory
    wav_name = wav_path.name if wav_name_out is None else wav_name_out
    tg_name = tg_path.name if tg_name_out is None else tg_name_out
    shutil.copy(wav_path, input_mfa_dir / wav_name)
    shutil.copy(tg_path, input_mfa_dir / tg_name)


def loadAnnotsToDict(annot_dir: str, tier_name: Union[str, list[str]] =
                     ['words', 'phones']) -> dict:
    """Load text annotation files with the format:
    start_time    end_time    label
    from the specified directory to a dictionary. Only text files
    of the format '*_{tier}.txt' will be loaded for each tier specified in the
    tier_name argument.

    Args:
        annot_dir (str): Path to the directory containing annotation files.
        tier_name (Union[str, list[str]], optional): Annotation levels to load.
        See main blurb above for how tier names affect file loading.
        Defaults to ['words', 'phones'].

    Returns:
        dict: Dictionary containing annotation data separated by tier.
            Each tier will have a separate subdictionary in the main returned
            dictionary. Within each tier subdictionary, the keys are the
            annotation labels (e.g. 'dog', 'hoot' for sentence rep stimuli).
            The values are lists of lists, where each sublist contains the
            start time, end time, and label for an annotation.

            e.g. getting the first phoneme level annotation for the stimuli
            'dog' (which would be loaded from 'dog_phones.txt'):
            annot_dict['phones']['dog'][0] = [0.0, 0.1, 'd']

    """    
    annot_dir = Path(annot_dir)

    # Ensure tier_name is a list for iteration
    if not isinstance(tier_name, list):
        tier_name = [tier_name]

    # collect annotation files to read
    to_load = []
    annot_dict = {}
    for tier in tier_name:
        to_load.extend(glob.glob((annot_dir / f'*_{tier}.txt').as_posix()))
        annot_dict[tier] = {}  # each tier will be a subdict

    # read annotation files and separate by tier
    for annot_file in to_load:
        tier = annot_file.split('_')[-1].split('.')[0]
        label = os.path.basename(annot_file).split('_')[0]
        with open(annot_file, 'r') as f:
            rows = []
            for line in f:
                rows.append(line.strip().split('\t'))
            annot_dict[tier][label] = rows
    
    return annot_dict


def mergeAnnots(annot_path: str, merge_thresh: float,
                 merge_path: Optional[str] = None,
                 merge_name: str = 'merged_stim_times') -> None:
    """Merge annotations that are close together in time.

    Args:
        annot_path (str): Path to separated annotation file
        merge_thresh (float): Threshold in seconds for merging stimuli. The
            threshold is the maximum time difference between two stimuli (end
            of first stimulus to start of second stimulus) for them to be
            considered part of the same stimulus.
        merge_path (Optional[str], optional): Path for the merged file to be
        saved to. Uses the same directory (with name specified in `merge_name`
        arg if this is None). Defaults to None.
        merge_name (str, optional): Name for merged file in the case that no
        path is specified (see above). Defaults to 'merged_stim_times.txt'.
    """    
    
    # use annotation directory if no merge path is specified
    if merge_path is None:
        merge_path = Path(annot_path).parent / (merge_name + '.txt')

    with open(annot_path, 'r') as f:
        stim_times = f.readlines()
    stim_times = [line.strip().split('\t') for line in stim_times]

    # set starting stimulus as initial point
    merged_stims = [stim_times[0]]
    for i in range(1, len(stim_times)):
        _, curr_e, _ = merged_stims[-1]  # current stim we are building
        next_s, next_e, next_stim = stim_times[i]  # next stim to consider

        if np.abs(float(next_s) - float(curr_e)) < merge_thresh:
            # update end time and stimulus text if times are close enough
            merged_stims[-1][1] = next_e
            merged_stims[-1][2] += ' ' + next_stim
        else:
            # add new stimulus instance if times are too far apart
            merged_stims.append(stim_times[i])
    
    with open(merge_path, 'w') as f:
        for stim in merged_stims:
            f.write('\t'.join(stim) + '\n')


def annotateStims(annot_dict: dict, onset_path: str, trial_info_path: str,
                  task_name: str, out_dir: str = None,
                  out_form: str = "mfa_stim_%s.txt") -> None:
    """Places stim annotation templates in a patient's label file at locations
    defined by the provdied cue consets.

    Args:
        annot_dict (dict): Stim annotation templates. See format in
            loadAnnots() function above.
        onset_path (str): Path to the cue onset file for the patient.
        trial_info_path (str): Path to the trial info file for the patient.
        task_name (str): Name of the task being run.
        out_dir (str, optional): Directory to save label files to. If None,
            will add a directory "mfa" to the directory containing the onsets.
            Defaults to None.
        out_form (str, optional): Format to save label files in. Defaults to
        "mfa_stim_%s.txt".
    """    
    onset_path = Path(onset_path)

    # use mfa dir in same directiory as onset file if no output directory is
    # specified
    if out_dir is None:
        out_dir = onset_path.parent / 'mfa'

        # # add mfa directory if it doesn't exist
        # if not out_dir.exists():
        #     out_dir.mkdir()

    # get all of the cue onsets
    with open(onset_path, 'r') as f:
        onsets = f.readlines()
        # separate onsets into start time, end time, and stimulus
        onsets = [line.strip().split('\t') for line in onsets]

    # get the stimulus modality type (only relevant for picture naming task)
    if task_name == 'picture_naming':
        mod_cnds = loadMatCol(trial_info_path, 'trialInfo', 'modality')
    else:
        mod_cnds = ['sound'] * len(onsets)

    # iterate through each annotation tier
    tier_names = list(annot_dict.keys())
    
    for tier in tier_names:
        # create label file for current tier
        try:
            fname = out_dir / (out_form % tier)
        except TypeError:
            fname = out_dir / (out_form.split('.')[0] + tier + '.txt')
        with open(fname, 'w') as f:
            for i, (cue_start, cue_stop, stim) in enumerate(onsets):
                # stim = stim.split('_')[1]
                stim = stim.split('_')[1].split('.')[0]
                # use sound annotations for auditory stimuli
                if mod_cnds[i] == 'sound':
                    try:
                        curr_annots = annot_dict[tier][stim]
                    except KeyError:
                        print(f'No annotations found for {stim} in tier {tier}.')
                        continue
                    # write all tokens corresponding to the current stimulus
                    for (annot_start, annot_stop, token) in curr_annots:
                        f.write(f'{float(cue_start) + float(annot_start)}\t'
                                f'{float(cue_start) + float(annot_stop)}\t'
                                f'{token}\n')
                # use cue annotations otherwise
                else:
                    f.write(f'{cue_start}\t{cue_stop}\t{stim}\n')
                    

def annotateResp(time_path: str, trial_info_path: str, recording_length: float,
                 output_dir: str, max_dur: float, task_name: str,
                 method: str = 'resp',
                 output_fname: str = 'annotated_resp_windows.txt') -> None:
    """Create response windows for a patient's recording based on the provided
    stimulus timing information and trial info.

    Args:
        time_path (str): Path to the stimulus timing file.
        trial_info_path (str): Path to the trial info file.
        recording_length (float): Length of the recording in seconds.
        output_dir (str): Directory to save the response windows to.
        max_dur (float): Maximum duration of a response window in seconds.
        task_name (str): Name of the task being run.
        method (str, optional): Method to use for response windows. 'resp' will
            create response windows based on the stimulus content. 'yes' or
            'no' will create response windows assuming the patient is only
            responding with 'yes' or 'no' (for yes/no tasks). Defaults to
            'resp'.
        output_fname (str, optional): Name of the output file containing the
            response windows. Defaults to 'annotated_resp_windows.txt'.
    """
    # load stimulus timing information and trial info information
    # time_path = base_dir / time_fname
    # trial_info_path = base_dir / trials_fname

    # covnert stim times to list of format [start, end, stim]
    stim_times = open(time_path, 'r').readlines()
    stim_times = [line.strip().split('\t') for line in stim_times]

    # extract cue type condtions from trial info
    cue_cnds = loadMatCol(trial_info_path, 'trialInfo', 0)

    # extract go conditions from trial info
    if task_name == 'picture_naming':
        # go cnds not defined in trial info for picture naming task, for
        # compatibility with other tasks
        go_cnds = ['Speak'] * len(cue_cnds)
    # intraop task trial info doesn't contain this info, but all are repeat
    # - defining these for compatibility
    elif task_name == 'lexical_repeat_intraop':
        go_cnds = ['Speak'] * len(cue_cnds)
        cue_cnds = ['Listen'] * len(cue_cnds)
    else:
        go_cnds = loadMatCol(trial_info_path, 'trialInfo', 2)

    out_path = output_dir / output_fname
    with open(out_path, 'w') as f:
        for i in range(len(stim_times)):
            # check that response is expected by task conditions
            if method == 'resp':
                if go_cnds[i] != 'Speak' or cue_cnds[i] not in ['Repeat', 'Listen', 'ListenSpeak']:
                    continue
                _, stim_e1, stim = stim_times[i]
            elif method in ['yes', 'no']:
                if go_cnds[i] != 'Speak' or cue_cnds[i] != 'Yes/No':
                    continue
                _, stim_e1, _ = stim_times[i]
                stim = method

            if i == len(stim_times) - 1:
                # last response window is from the end of the last stimulus to
                # the end of the recording
                stim_s2 = recording_length  # in seconds
            else:
                stim_s2, _, _ = stim_times[i + 1]

            # write the response window
            stim_e1 = float(stim_e1)
            stim_s2 = float(stim_s2)
            if stim_s2 - stim_e1 > max_dur:
                stim_s2 = stim_e1 + max_dur
            f.write(f'{stim_e1}\t{stim_s2}\t{stim}\n')

def annotateRetrocue(time_path: str, recording_length: float,
                     output_dir: str, max_dur: float, 
                     output_fname: str = 'annotated_resp_windows.txt') -> None:
    """Create retrocue task response windows for a patient's recording based
    on the provided stimulus timing information.

    Args:
        time_path (str): Path to the stimulus timing file.
        recording_length (float): Length of the recording in seconds.
        output_dir (str): Directory to save the response windows to.
        max_dur (float): Maximum duration of a response window in seconds.
        output_fname (str, optional): Name of the output file containing the
            response windows. Defaults to 'annotated_resp_windows.txt'.
    """
    # load stimulus timing information and trial info information
    # time_path = base_dir / time_fname
    # trial_info_path = base_dir / trials_fname

    # covnert stim times to list of format [start, end, stim]
    stim_times = open(time_path, 'r').readlines()
    stim_times = [line.strip().split('\t') for line in stim_times]

    out_path = output_dir / output_fname
    with open(out_path, 'w') as f:
        for i in range(len(stim_times)):
            # ignore lines with no label
            if len(stim_times[i]) < 3:
                continue

            _, stim_e1, stim = stim_times[i]

            if i == len(stim_times) - 1:
                # last response window is from the end of the last stimulus to
                # the end of the recording
                stim_s2 = recording_length  # in seconds
            else:
                stim_s2 = stim_times[i + 1][0]

            # write the response window
            stim_e1 = float(stim_e1)
            stim_s2 = float(stim_s2)
            if stim_s2 - stim_e1 > max_dur:
                stim_s2 = stim_e1 + max_dur
            f.write(f'{stim_e1}\t{stim_s2}\t{stim}\n')
                    
def runMFA(input_mfa_dir: str, output_mfa_dir: str,
           mfa_dict: str = 'english_us_arpa',
           mfa_model: str = 'english_us_arpa',
           single_speaker=False) -> bool:
    """Run Montreal Forced Aligner (MFA) on the provided input directory.

    Args:
        input_mfa_dir (str): Path to the directory containing audio and
            transcript files for MFA.
        output_mfa_dir (str): Path to the directory where MFA output files will
            be saved.
        mfa_dict (str, optional): Name of dictionary to use for MFA.
            Defaults to 'english_us_arpa'.
        mfa_model (str, optional): Name of acoustic model to use for MFA.
            Defaults to 'english_us_arpa'.
        single_speaker (bool, optional): Flag to indicate if the audio is from
            a single speaker. Defaults to True.
    """    
    try:
        # os.system(f'mfa align --clean {input_mfa_dir} {mfa_dict} {mfa_model} '
        #         f'{output_mfa_dir}')
        mfa_cmd = ['mfa', 'align', '--clean', input_mfa_dir, mfa_dict,
                   mfa_model, output_mfa_dir]
        if single_speaker:
            mfa_cmd.insert(3, '--single_speaker')
        subprocess.run(mfa_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running MFA: {e}")
        return False
    return True
    
def loadMatCol(mat_path: str, key: str, col: Union[int, str]) -> np.ndarray:
    """Load a column from a variable in a .mat file.

    Args:
        mat_path (str): Path to mat file.
        key (str): Name of the variable in the mat file.
        col (int, str): Identifier of column to extract from the mat data.
            If an integer, this is the index of the column. If a string, this
            is the name of the column.

    Returns:
        np.ndarray: Column of data from the mat file.
    """    
    data = sio.loadmat(mat_path)
    data_var = data[key][0,:]
    try:  # trial info mat file saved as cell
        data_col = np.array([row[0,0][col][0] if row[0,0][col].shape[0] > 0
                             else '' for row in data_var])
    except IndexError:  # trial info mat file saved as struct
        data_col = np.array([row[col][0] if row[col].shape[0] > 0 else ''
                             for row in data_var])
    return data_col

# if __name__ == '__main__':
#     runMFA('test', 'test')