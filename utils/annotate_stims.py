from pathlib import Path
import glob

from mfa_utils import loadAnnotsToDict, annotateStims

def main():
    # pt_dir = r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\response_coding\response_coding_results\SentenceRep'
    # pts = glob.glob(pt_dir + '/D*')
    # annot_dir = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\SentenceRep\SentenceRep_Stim\mfa\stim_annotations')

    # pt_dir = r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\response_coding\response_coding_results\Phoneme_Sequencing'
    # pts = glob.glob(pt_dir + '/D*')
    # annot_dir = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\mfa\stim_annotations')

    # pt_dir = r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\response_coding\response_coding_results\Phoneme_Sequencing\intraop'
    pt_dir = r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\response_coding\response_coding_results\Phoneme_Sequencing\intraop\no_kumar_phoneme'
    pts = glob.glob(pt_dir + '/S*')
    annot_dir = Path(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\Stim\PhonemeSequencing\all_tokens\mfa\stim_annotations')

    annot_dict = loadAnnotsToDict(annot_dir)
    for pt in pts:
        onset_path = Path(pt) / 'cue_events.txt'
        annotateStims(annot_dict, onset_path, out_form='mfa_stim_%s.txt')

if __name__ == '__main__':
    main()