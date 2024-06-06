# %% Imports and definitions
import os
import shutil
from pathlib import Path
import numpy as np
import glob
from omegaconf import OmegaConf

from mfa_utils import txt2textGrid, textGrid2txt, calculateAudDur


# %% Get stimuli to annotate
task = 'sentence_repetition'
stim_text_dict = OmegaConf.load(f'conf/task/{task}.yaml')['cue_text']
print(list(stim_text_dict.items()))

# sentence rep
# stim_text_dict['mice'] = 'there was once a house that was overrun with mice'
# stim_text_dict['dog'] = 'the dog was very proud of the bell'
# stim_text_dict['fame'] = 'notoriety is often mistaken for fame'
# rel_stims = ['heat.wav', 'hoot.wav', 'hot.wav', 'hut.wav']

if task == 'sentence_repetition':
    stim_wavs = glob.glob(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\*.wav')
elif task == 'phoneme_sequencing':
    stim_wavs = glob.glob(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\*.wav')
else:
    raise NotImplementedError(f'Task {task} not implemented')

# for stim in stim_wavs:
#     stim_name = stim.split('\\')[-1]
#     if stim_name in rel_stims:
#         # print(stim)
#         stim_text = stim_name.split('.')[0]
#         stim_text_dict[stim_text] = stim_text

# phoneme sequencing
# stim_wavs = glob.glob(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\*.wav')

# for stim in stim_wavs:
#     stim_name = stim.split('\\')[-1]
#     # print(stim)
#     stim_text = stim_name.split('.')[0]
#     stim_text_dict[stim_text] = stim_text


# %% Generate transcripts for each stimulus
stim_dur_dict = {}
for stim in stim_wavs:
    stim_name = stim.split('\\')[-1].split('.')[0].lower()
    if stim_name in stim_text_dict.keys():
        stim_dur = calculateAudDur(stim)
        stim_dur_dict[stim_name] = stim_dur

for k,v in stim_text_dict.items():
    # txt_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\transcripts\{}.txt'.format(k))
    txt_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\mfa\transcripts\{}.txt'.format(k))
    with open(txt_path, 'w+') as f:
        # round to 3 decimal places and don't go over the duration of the audio
        end = np.floor(stim_dur_dict[k]*1000) / 1000
        # end = stim_dur_dict[k] + 0.01
        # print(f'0.0\t{end}\t{v}')
        f.write(f'0.0\t{end}\t{v}')


# %% Convert transcripts to TextGrids
for k,v in stim_text_dict.items():
    # txt_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\transcripts\{}.txt'.format(k))
    txt_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\mfa\transcripts\{}.txt'.format(k))

    tg_name = k
    txt2textGrid(txt_path, tg_name, tg_path=None, tier_name='words', return_tg=False)

# %% Prepare MFA folder structure

# TODO: move logic to prepare_mfa() in mfa_utils.py
for k,v in stim_text_dict.items():
    # base_dir = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\mfa_prep')
    base_dir = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\mfa\mfa_prep')

    input_mfa_dir = base_dir / k / 'input_mfa'
    output_mfa_dir = base_dir / k / 'output_mfa'

    os.makedirs(input_mfa_dir, exist_ok=True)
    os.makedirs(output_mfa_dir, exist_ok=True)

    # wav_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\{}.wav'.format(k))
    wav_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\{}.wav'.format(k))
    wav_name = k + '.wav'
    shutil.copy(wav_path, input_mfa_dir / wav_name)

    # tg_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\transcripts\{}.TextGrid'.format(k))
    tg_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\mfa\transcripts\{}.TextGrid'.format(k))
    tg_name = k + '.TextGrid'
    shutil.copy(tg_path, input_mfa_dir / tg_name)

# %% Run MFA and convert output to txt files

for k,v in stim_text_dict.items():
    ### Running MFA ###
    # input_mfa_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\mfa_prep\{}'.format(k)) / 'input_mfa'
    # output_mfa_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\mfa_prep\{}'.format(k)) / 'output_mfa'

    input_mfa_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\mfa\mfa_prep\{}'.format(k)) / 'input_mfa'
    output_mfa_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\mfa\mfa_prep\{}'.format(k)) / 'output_mfa'

    # os.system(f'mfa align --clean {input_mfa_path} english_us_arpa english_us_arpa {output_mfa_path}')
    os.system(f'mfa align --clean {input_mfa_path} english_us_ps english_us_arpa {output_mfa_path}')
    # os.system(f'mfa align --clean {input_mfa_path} english_us_mfa english_mfa {output_mfa_path}')

    ### Convert MFA output textgrids to txt files ###
    # output_tg_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\mfa_prep\{}'.format(k)) / 'output_mfa' / f'{k}.TextGrid'
    # output_txt_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\stim_annotations') / f'{k}'

    output_tg_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\mfa\mfa_prep\{}'.format(k)) / 'output_mfa' / f'{k}.TextGrid'
    output_txt_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\mfa\stim_annotations') / f'{k}'

    textGrid2txt(output_tg_path, k, txt_path=output_txt_path, tier_name=['words', 'phones'])


# for k,v in stim_text_dict.items():
#     output_tg_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\mfa_prep\{}'.format(k)) / 'output_mfa' / f'{k}.TextGrid'
#     output_txt_path = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\stim_annotations') / f'{k}'

#     textGrid2txt(output_tg_path, k, txt_path=output_txt_path, tier_name=['words', 'phones'])