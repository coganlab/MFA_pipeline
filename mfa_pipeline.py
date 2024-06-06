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
    
    if cfg.task.name not in ['phoneme_sequencing', 'sentence_repetition']:
        raise NotImplementedError(f'Task {cfg.task.name} not implemented')
    
    if cfg.patients == 'all':
        print('========== Running MFA on all patients in directory ==========')
        # only access patient folders
        patients = []
        for prefix in cfg.patient_prefixes:
            patients += glob.glob(os.path.join(cfg.patient_dir, prefix))
        patients = [os.path.basename(patient) for patient in patients]
    else:
        print('=========== Running MFA on selected patients ===========')
        patients = cfg.patients.split(',')

    start = time.time()
    err_pts = []
    for pt in tqdm(patients, desc='Running MFA', ascii=False, ncols=1000,
                   bar_format='{l_bar}{bar}{r_bar}'):
        pt_path = Path(cfg.patient_dir) / pt
        mfa_path = pt_path / 'mfa'
        
        ### for large-scale patient runs, where you want the script to continue
        ### to the next patient if an error occurs
        if not cfg.debug_mode:
            try:
                try:
                    # load merge stim annotations together for different words
                    # in same stim
                    mfa_utils.mergeAnnots(mfa_path / 'mfa_stim_words.txt',
                                          cfg.merge_thresh, merge_path=pt_path /
                                          'merged_stim_times.txt')
                except FileNotFoundError:
                    print(f'Stimulus annotations not found for {pt}. Please '
                          'use the annotate_stims.py script to create them or '
                          'the a previous version of the mfa pipeline that '
                          'does not rely on stimulus annotations '
                          '(less accurate).')
                    err_pts.append(pt)
                    continue

                # create text grid annotation for responses
                recording_dur = mfa_utils.calculateAudDur(pt_path /
                                                          'allblocks.wav')
                mfa_utils.annotateResp(pt_path, recording_dur, mfa_path,
                                       cfg.task.max_dur)
                mfa_utils.txt2textGrid(mfa_path / 'annotated_resp_windows.txt',
                                       'allblocks', tg_dir=pt_path)
                mfa_utils.prepareForMFA(mfa_path, wav_path=pt_path /
                                        'allblocks.wav', tg_path=pt_path /
                                        'allblocks.TextGrid')

            except Exception as e:
                print(f'********** Error preparing patient {pt} for MFA: '
                      f'**********\n{e}')
                err_pts.append(pt)
                continue

                # run mfa
            mfa_ran = mfa_utils.runMFA(mfa_path / 'input_mfa', mfa_path /
                                       'output_mfa', mfa_dict=cfg.task.mfa.dict,
                                       mfa_model=cfg.task.mfa.acoustic)
            if not mfa_ran:
                print(f'********** Error running MFA on patient {pt} ***'
                      '*******')
                err_pts.append(pt)
                continue
            try:
                # convert mfa output to txt file
                mfa_utils.textGrid2txt(mfa_path / 'output_mfa' /
                                       'allblocks.TextGrid', 'mfa_resp',
                                       txt_dir=mfa_path)
            except Exception as e:
                print('********** Error extracting annotations for patient '
                      f'{pt}: **********\n{e} ')
                err_pts.append(pt)
                continue
        #### for investigating errors ####
        else:
            print('##### RUNNING IN DEBUG MODE #####')
            mfa_utils.mergeAnnots(mfa_path / 'mfa_stim_words.txt',
                                  cfg.merge_thresh, merge_path=pt_path /
                                  'merged_stim_times.txt')
            recording_dur = mfa_utils.calculateAudDur(pt_path /
                                                      'allblocks.wav')
            mfa_utils.annotateResp(pt_path, recording_dur, mfa_path,
                                   cfg.task.max_dur)
            mfa_utils.txt2textGrid(mfa_path / 'annotated_resp_windows.txt',
                                   'allblocks', tg_dir=pt_path)
            mfa_utils.prepareForMFA(mfa_path, wav_path=pt_path /
                                    'allblocks.wav', tg_path=pt_path /
                                    'allblocks.TextGrid')
            mfa_utils.runMFA(mfa_path / 'input_mfa', mfa_path /
                             'output_mfa')
            mfa_utils.textGrid2txt(mfa_path / 'output_mfa' /
                                   'allblocks.TextGrid', 'mfa_resp',
                                   txt_dir=mfa_path)

    end = time.time()
    if len(err_pts) > 0:
        print(f'Errors occurred for the following patients: \n{err_pts}')
    print(f'Finished processing {len(patients)} patients in {end-start} '
          'seconds')
            

if __name__ == '__main__':
    main()