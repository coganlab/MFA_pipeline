import glob
from pathlib import Path

files_to_keep = ['mfa_resp_phones.txt', 'mfa_resp_words.txt',
                 'mfa_stim_phones.txt', 'mfa_stim_words.txt',
                 'annotated_resp_windows.txt', 'annotations_of_interest',
                 'input_mfa', 'output_mfa']

# pts = glob.glob(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\response_coding\response_coding_results\SentenceRep\D*')
# pts = glob.glob(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\response_coding\response_coding_results\Phoneme_Sequencing\intraop\S33')
# pts = glob.glob(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\response_coding\response_coding_results\Phoneme_Sequencing\D*')
pts = glob.glob(r'C:\Users\zms14\Box\CoganLab\ECoG_Task_Data\response_coding\response_coding_results\Phoneme_Sequencing\intraop\no_kumar_phoneme\S*')
for pt in pts:
    mfa_dir = Path(pt) / 'mfa'

    Path.mkdir(mfa_dir / 'old', exist_ok=True)

    for file in mfa_dir.iterdir():
        if file.name == 'old':
            continue
        # elif file.is_dir() and file.name not in ['input_mfa', 'output_mfa']:
        elif file.is_dir():
            # for subfile in file.iterdir():
            #     try:
            #         subfile.unlink()
            #     except PermissionError:
            #         continue
                # print('Delete:', subfile.name)
                # file.replace(mfa_dir / 'old' / file.name)
                print('Move to old:', file.name)
        elif file.name not in files_to_keep:
            # try:
            #     file.unlink()
            # except PermissionError:
            #     continue
            print('Delete:', file.name)
        else:
            # file.replace(mfa_dir / 'old' / file.name)
            print('Move to old:', file.name)