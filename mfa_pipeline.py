import os
from pathlib import Path
import time
import glob
from tqdm import tqdm
import hydra
from omegaconf import DictConfig, OmegaConf
from utils import mfa_utils


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:

    missing_keys: set[str] = OmegaConf.missing_keys(cfg)
    if missing_keys:
        raise RuntimeError(f'Missing mandatory key(s):\n{missing_keys}\n '
                           'Please specify them in the command line or config '
                           'file.')
    
    if cfg.patients == 'all':
        print('========== Running MFA on all patients in directory ==========')
        # only access patient folders
        patients = []
        for prefix in cfg.patient_prefixes:
            patients += glob.glob(os.path.join(cfg.patient_dir, prefix))
        patients = [os.path.basename(patient) for patient in patients]
    else:
        patients = cfg.patients.split(',')
        print(f'========== Running MFA on seletected patients: {patients}'
              '==========')


    print(f'##### Running MFA for task: {cfg.task.name} #####')

    if cfg.debug_mode:
        print('##### RUNNING IN DEBUG MODE #####')

    HOME = os.path.expanduser("~")
    run_stim = cfg.task.get('run_stim', True)      

    run_type = ['resp']
    if cfg.task.get('mark_yes_no', False):
        run_type.append('yes')
        run_type.append('no')

    start = time.time()
    err_pts = []
    for pt in tqdm(patients, desc='Running MFA', ascii=False, ncols=150,
                   bar_format='{l_bar}{bar}{r_bar}'):
        pt_path = Path(cfg.patient_dir) / pt
        mfa_path = pt_path / 'mfa'
        mfa_utils.makeMFADirs(pt_path, run_type)

        if run_stim:
            print('##### Annotating stimuli for patient %s #####' % pt)
            # Load stimulus annotations for the task
            annot_dir = Path(os.path.join(HOME, cfg.task.stim_dir))
            annot_dict = mfa_utils.loadAnnotsToDict(annot_dir)

            stims_ran, err_msg = run_stims(annot_dict, pt_path,
                                           mfa_path, cfg.merge_thresh,
                                           cfg.debug_mode)
            if not stims_ran:
                err_pts.append(pt)
                print(err_msg % pt)
                continue

            if cfg.only_stims:
                continue

        for t in run_type:
            t_msg = 'Response' if t == 'resp' else 'Yes & No'
            print(f'##### Preparing patient {pt} for MFA: {t_msg} '
                  'Annotation #####')
            annot_fname = cfg.task.get('annot_fname')
            resp_ran, err_msg = run_resp(cfg.task.name, pt_path, mfa_path, t,
                                         cfg.task.max_dur, cfg.task.mfa.dict,
                                         cfg.task.mfa.acoustic,
                                         cfg.debug_mode, annot_fname)
            if not resp_ran:
                err_pts.append(pt)
                print(err_msg % pt)
                continue

    end = time.time()
    if len(err_pts) > 0:
        print(f'Errors occurred for the following patients: \n{err_pts}')
    print(f'Finished processing {len(patients)} patients in {end-start} '
          'seconds')


def run_stims(annot_dict, pt_path, mfa_path, merge_thresh, debug):
    # relevant files in patient directory
    onset_path = pt_path / 'cue_events.txt'
    trial_info_path = pt_path / 'trialInfo.mat'

    if not debug:
        try:
            # annotate stimuli for the current patient
            mfa_utils.annotateStims(annot_dict, onset_path, trial_info_path,
                                    out_form='mfa_stim_%s.txt')

            # merge stimuli annotations together so that separate
            # intrastimulus words are represented as the same stimulus
            mfa_utils.mergeAnnots(
                mfa_path / 'mfa_stim_words.txt',
                merge_thresh,
                merge_path=mfa_path / 'merged_stim_times.txt'
            )
        except Exception as e:
            err_msg = f'Error annotating stimuli for patient %s: {e}'
            return False, err_msg
    else:
        mfa_utils.annotateStims(annot_dict, onset_path, trial_info_path,
                                out_form='mfa_stim_%s.txt')
        mfa_utils.mergeAnnots(mfa_path / 'mfa_stim_words.txt',
                              merge_thresh, merge_path=mfa_path /
                              'merged_stim_times.txt')
    return True, None


def run_resp(task_name, pt_path, mfa_path, resp_type, max_dur, mfa_dict,
             mfa_acoustic, debug, annot_name=None):
    # default annotation file name if one is not provided
    if not annot_name:
        annot_name = f'annotated_{resp_type}_windows.txt'
    wav_name_out = (f'allblocks_{resp_type}.wav' if resp_type in ['yes', 'no']
                    else 'allblocks.wav')
    tg_out = (f'allblocks_{resp_type}.TextGrid' if resp_type in ['yes', 'no']
              else 'allblocks.TextGrid')
    inp_mfa_name = (f'input_mfa_{resp_type}' if resp_type in ['yes', 'no']
                    else 'input_mfa')
    out_mfa_name = (f'output_mfa_{resp_type}' if resp_type in ['yes', 'no']
                    else 'output_mfa')
    label_name = f'mfa_{resp_type}'
    if not debug:
        try:
            # create text grid annotation for responses            
            if task_name == 'retro_cue':
                # create text grid annotation for retro cue task
                mfa_utils.annotateRetrocue(pt_path / 'cue_events_mfa.txt',
                                           recording_dur,
                                           mfa_path, max_dur,
                                           output_fname=annot_name)
            else:
                recording_dur = mfa_utils.calculateAudDur(
                                    pt_path / 'allblocks.wav')
                mfa_utils.annotateResp(mfa_path / 'merged_stim_times.txt.',
                                    pt_path / 'trialInfo.mat',
                                    recording_dur, mfa_path,
                                    max_dur, method=resp_type,
                                    output_fname=annot_name)

            mfa_utils.txt2textGrid(mfa_path / annot_name, tg_out,
                                   tg_dir=mfa_path)
            mfa_utils.prepareForMFA(mfa_path,
                                    wav_path=pt_path / 'allblocks.wav',
                                    tg_path=mfa_path / tg_out,
                                    wav_name_out=wav_name_out,
                                    input_dir_name=inp_mfa_name,
                                    output_dir_name=out_mfa_name)

        except Exception as e:
            err_msg = f'Error preparing patient %s for MFA: {e}'
            return False, err_msg

        # run mfa
        mfa_ran = mfa_utils.runMFA(mfa_path / inp_mfa_name, mfa_path /
                                   out_mfa_name, mfa_dict=mfa_dict,
                                   mfa_model=mfa_acoustic)
        if not mfa_ran:
            err_msg = f'Error running MFA on patient %s'
            return False, err_msg
        try:
            # convert mfa output to txt file
            mfa_utils.textGrid2txt(mfa_path / out_mfa_name /
                                   tg_out, label_name, txt_dir=mfa_path)
        except Exception as e:
            err_msg = f'Error extracting annotations for patient %s: {e}'
            return False, err_msg

    else:
        # create text grid annotation for responses
        recording_dur = mfa_utils.calculateAudDur(
                                pt_path / 'allblocks.wav')
        # create text grid annotation for responses            
        if task_name == 'retro_cue':
            # create text grid annotation for retro cue task
            mfa_utils.annotateRetrocue(pt_path / 'cue_events_mfa.txt',
                                        recording_dur,
                                        mfa_path, max_dur,
                                        output_fname=annot_name)
        else:
            recording_dur = mfa_utils.calculateAudDur(
                                pt_path / 'allblocks.wav')
            mfa_utils.annotateResp(mfa_path / 'merged_stim_times.txt.',
                                pt_path / 'trialInfo.mat',
                                recording_dur, mfa_path,
                                max_dur, method=resp_type,
                                output_fname=annot_name)

        mfa_utils.txt2textGrid(mfa_path / annot_name, tg_out,
                               tg_dir=mfa_path)
        mfa_utils.prepareForMFA(mfa_path, wav_path=pt_path / 'allblocks.wav',
                                tg_path=mfa_path / tg_out,
                                wav_name_out=wav_name_out,
                                input_dir_name=inp_mfa_name,
                                output_dir_name=out_mfa_name)
        _ = mfa_utils.runMFA(mfa_path / inp_mfa_name, mfa_path /
                             out_mfa_name, mfa_dict=mfa_dict,
                             mfa_model=mfa_acoustic)
        # convert mfa output to txt file
        mfa_utils.textGrid2txt(mfa_path / out_mfa_name / tg_out, label_name,
                               txt_dir=mfa_path)
    return True, None


if __name__ == '__main__':
    main()