import os
import traceback
import argparse
from BugInvestigator import BugInvestigator
from CodeProcessor import CodeProcessor
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.preprocessing import MultiLabelBinarizer
import numpy as np

def find_leaf_dirs_with_bug_fix(base_dir):
    """
    Yield leaf directories (no subdirectories) containing at least one 'bug*.py' and one 'fix*.py'.
    """
    for dirpath, dirnames, filenames in os.walk(base_dir):
        if not dirnames:
            bug_files = [f for f in filenames if 'bug' in f.lower() and f.endswith('.py')]
            fix_files = [f for f in filenames if 'fix' in f.lower() and f.endswith('.py')]
            if bug_files and fix_files:
                yield dirpath, bug_files, fix_files


def infer_label(bugErrorMessage):
    """
    Map detected errors to one of the three labels:
    - Unitary errors -> 'Operator-related'
    - Measurement errors -> 'Measurement-related'
    - Initialization errors -> 'Qubit/Initialization-related'
    Otherwise -> 'not a bug'
    """
    # if bugErrorMessage.get('Unitary') and bugErrorMessage['Unitary'] != 'None':
    #     return 'Operator-related'
    # if bugErrorMessage.get('Measurement') and bugErrorMessage['Measurement'] != 'None':
    #     return 'Measurement-related'
    # if bugErrorMessage.get('Initialization') and bugErrorMessage['Initialization'] != 'None':
    #     return 'Qubit/Initialization-related'

    # if bugErrorMessage.get('Initialization') and bugErrorMessage['Initialization'] != 'None':
    #     return 'Initialization'
    # if bugErrorMessage.get('IncorrectInit') and bugErrorMessage['IncorrectInit'] != 'None':
    #     return 'IncorrectInit'
    # if bugErrorMessage.get('IncorrectRegisters') and bugErrorMessage['IncorrectRegisters'] != 'None':
    #     return 'IncorrectRegisters'
    # if bugErrorMessage.get('Measurement') and bugErrorMessage['Measurement'] != 'None':
    #     return 'Measurement'
    # if bugErrorMessage.get('IncorrectMeasurement') and bugErrorMessage['IncorrectMeasurement'] != 'None':
    #     return 'IncorrectMeasurement'
    # if bugErrorMessage.get('IncorrectNumberOfSamples') and bugErrorMessage['IncorrectNumberOfSamples'] != 'None':
    #     return 'IncorrectNumberOfSamples'
    # if bugErrorMessage.get('IncorrectDecisionToMeasure') and bugErrorMessage['IncorrectDecisionToMeasure'] != 'None':
    #     return 'IncorrectDecisionToMeasure'
    # if bugErrorMessage.get('Unitary') and bugErrorMessage['Unitary'] != 'None':
    #     return 'Unitary'
    # if bugErrorMessage.get('IncorrectGate') and bugErrorMessage['IncorrectGate'] != 'None':
    #     return 'IncorrectGate'
    # if bugErrorMessage.get('IncorrectHadamard') and bugErrorMessage['IncorrectHadamard'] != 'None':
    #     return 'IncorrectHadamard'
    # if bugErrorMessage.get('RootDetector') and bugErrorMessage['RootDetector'] != 'None':
    #     return 'RootDetector'
    # return 'not a bug'
    
    # pred_label = []
    # for bugType in ['IncorrectInit','IncorrectRegisters','IncorrectMeasurement','IncorrectNumberOfSamples','IncorrectDecisionToMeasure','IncorrectGate','IncorrectHadamard']:
    #     if bugErrorMessage[bugType]!='None':
    #         pred_label.append(bugType)
    # if(pred_label == []):
    #     pred_label.append('not a bug')
    # return pred_label

    pred_label = []

    if bugErrorMessage.get('Initialization') and bugErrorMessage['Initialization'] != 'None':
        pred_label.append('Initialization')
    if bugErrorMessage.get('IncorrectInit') and bugErrorMessage['IncorrectInit'] != 'None':
        pred_label.append('IncorrectInit')
    if bugErrorMessage.get('IncorrectRegisters') and bugErrorMessage['IncorrectRegisters'] != 'None':
        pred_label.append('IncorrectRegisters')
    if bugErrorMessage.get('Measurement') and bugErrorMessage['Measurement'] != 'None':
        pred_label.append('Measurement')
    if bugErrorMessage.get('IncorrectMeasurement') and bugErrorMessage['IncorrectMeasurement'] != 'None':
        pred_label.append('IncorrectMeasurement')
    if bugErrorMessage.get('IncorrectNumberOfSamples') and bugErrorMessage['IncorrectNumberOfSamples'] != 'None':
        pred_label.append('IncorrectNumberOfSamples')
    if bugErrorMessage.get('IncorrectDecisionToMeasure') and bugErrorMessage['IncorrectDecisionToMeasure'] != 'None':
        pred_label.append('IncorrectDecisionToMeasure')
    if bugErrorMessage.get('Unitary') and bugErrorMessage['Unitary'] != 'None':
        pred_label.append('Unitary')
    if bugErrorMessage.get('IncorrectGate') and bugErrorMessage['IncorrectGate'] != 'None':
        pred_label.append('IncorrectGate')
    if bugErrorMessage.get('IncorrectHadamard') and bugErrorMessage['IncorrectHadamard'] != 'None':
        pred_label.append('IncorrectHadamard')
    if bugErrorMessage.get('RootDetector') and bugErrorMessage['RootDetector'] != 'None':
        pred_label.append('RootDetector')

    if(pred_label == []):
        pred_label.append('not a bug')

    return pred_label


def encode_labels(labels, label_to_idx):
    vec = [0] * len(label_to_idx)
    for label in labels:
        vec[label_to_idx[label]] = 1
    return vec

def remove_comments(code):
    return "\n".join(
        line.split('#', 1)[0].rstrip().lstrip()
        for line in code.splitlines()
        if line.strip() and not line.strip().startswith('#')
    )


def main():
    parser = argparse.ArgumentParser(description="Process test case directories for bug/fix detection and evaluate metrics.")
    parser.add_argument(
        "--test-base-dir", 
        type=str,
        required=True,
        help="Path to the base directory containing test case subdirectories."
    )
    args = parser.parse_args()
    test_base_dir = args.test_base_dir

    # Initialize BugInvestigator
    bug_investigator = BugInvestigator("BugDetectors/config.json")
    bug_investigator.build_class_hierarchy()

    # Prepare lists for true and predicted labels
    y_true = []
    y_pred = []

    # true_label = []
    accuracy_array = []
    precision_array = []
    recall_array = []

    # Assigning values to each bug type
    all_labels = [
        # 'Initialization',
        'IncorrectInit',
        'IncorrectRegisters',
        # 'Measurement',
        'IncorrectMeasurement',
        'IncorrectNumberOfSamples',
        'IncorrectDecisionToMeasure',
        # 'Unitary',
        'IncorrectGate',
        'IncorrectHadamard',
        'ExcessiveMeasurements',
        # 'RootDetector',
        'not a bug',
        # 'Circuit-related',
        # 'Operator-related'   
    ]
    label_to_idx = {label: i for i, label in enumerate(all_labels)}

    # Iterate through all leaf dirs with both bug and fix files
    for dirpath, bug_files, fix_files in find_leaf_dirs_with_bug_fix(test_base_dir):
        true_label = []
        # read ground-truth label
        label_file = os.path.join(dirpath, 'label.txt')
        if not os.path.isfile(label_file):
            print(f"Skipping {dirpath}: no label.txt")
            continue
        with open(label_file, 'r') as lf:
            # true_label_subarray.extend(line.rstrip("\n") for line in lf)
            true_label.extend(line.rstrip("\n") for line in lf)
        
        # true_label.append(true_label_subarray)

        buggy_path = os.path.join(dirpath, bug_files[0])
        fixed_path = os.path.join(dirpath, fix_files[0])

        try:
            with open(buggy_path, 'r') as fb, open(fixed_path, 'r') as ff:
                buggy_code = fb.read()
                fixed_code = ff.read()

            buggy_code = remove_comments(buggy_code)
            fixed_code = remove_comments(fixed_code)

            test = CodeProcessor(buggy_code, fixed_code)
            bugErrorMessage = bug_investigator.detect_pattern(test)
            pred_label = infer_label(bugErrorMessage)

            mlb = MultiLabelBinarizer()
            mlb.fit(true_label + pred_label)  # get all possible labels

            print(f"Dir: {dirpath}")
            print(f"  True Label: {true_label}")
            print(f"  Pred Label: {pred_label}")

            y_true.append(true_label)
            y_pred.append(pred_label) 

            true_bin = [encode_labels(true_label, label_to_idx)]
            pred_bin = [encode_labels(pred_label, label_to_idx)]

            # accuracy = accuracy_score(true_bin, pred_bin)

            num = 0
            den = 0

            for actual_label, predicted_label in zip(true_bin[0], pred_bin[0]):
                if actual_label == predicted_label and actual_label != 0:
                    num += 1
                    den += 1
                elif actual_label != predicted_label:
                    den += 1
            
            accuracy = num / den if den > 0 else 0

            precision = precision_score(true_bin, pred_bin, average='micro')
            recall = recall_score(true_bin, pred_bin, average='micro')

            accuracy_array.append(accuracy)
            precision_array.append(precision)
            recall_array.append(recall)

        except Exception:
            print(f"ERROR AT {dirpath}")
            traceback.print_exc()

    if(accuracy_array):
        accuracy_array = np.array(accuracy_array)
        recall_array = np.array(recall_array)
        precision_array = np.array(precision_array)
        print("Average Accuracy = ", np.mean(accuracy_array))
        print("Average Recall = ", np.mean(recall_array))
        print("Average Precision = ", np.mean(precision_array))

    # Compute and print metrics
    # if y_true:
    #     acc = accuracy_score(y_true, y_pred)
    #     prec = precision_score(y_true, y_pred, average='macro', zero_division=0)
    #     rec = recall_score(y_true, y_pred, average='macro', zero_division=0)
    #     print("\nEvaluation Metrics:")
    #     print(f"  Accuracy: {acc:.4f}")
    #     print(f"  Precision: {prec:.4f}")
    #     print(f"  Recall: {rec:.4f}")
    # else:
    #     print("No labeled testcases processed.")

if __name__ == "__main__":
    main()