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
    pred_label = []
    for bugType in ['IncorrectInit','IncorrectRegisters','IncorrectMeasurement', 'ExcessiveMeasurements', 'IncorrectNumberOfSamples','IncorrectDecisionToMeasure','IncorrectStandardGate', 'IncorrectOpaqueGate', 'IncorrectHadamard', 'IncorrectUnitary']:
        if bugType in bugErrorMessage.keys() and bugErrorMessage[bugType]!='None':
            pred_label.append(bugType)
    if(pred_label == []):
        pred_label.append('not a bug')
    return pred_label


def encode_labels(labels, label_to_idx):
    vec = [0] * len(label_to_idx)
    for label in labels:
        if label in label_to_idx:  # Only encode labels that exist in label_to_idx
            vec[label_to_idx[label]] = 1
    return vec

def remove_comments(code):
    new_lines = []
    for line in code.splitlines():
        # Skip full-line comments
        if line.strip().startswith('#') or not line.strip():
            continue
        # Remove inline comments, but keep leading spaces
        if '#' in line:
            line = line.split('#', 1)[0]
        new_lines.append(line.rstrip())  # only strip the right side
    return "\n".join(new_lines)


def main():
    amt=0
    crt=0
    lbl=0
    mnf=0
    nab=0
    fail=0
    curr=[]
    working=[]
    lbled=[]
    failed=[]
    parser = argparse.ArgumentParser(description="Process test case directories for bug/fix detection and evaluate metrics.")
    parser.add_argument(
        "--test-base-dir", 
        type=str,
        required=True,
        help="Path to the base directory containing test case subdirectories."
    )
    args = parser.parse_args()
    test_base_dir = args.test_base_dir

    # Prepare lists for true and predicted labels
    y_true = []
    y_pred = []

    accuracy_array = []
    precision_array = []
    recall_array = []

    # Assigning values to each bug type
    all_labels = [
        'IncorrectInit',
        'IncorrectRegisters',
        'IncorrectMeasurement',
        'ExcessiveMeasurements',
        'IncorrectNumberOfSamples',
        'IncorrectDecisionToMeasure',
        'IncorrectStandardGate',
        'IncorrectOpaqueGate',
        'IncorrectHadamard',
        'IncorrectUnitary',
        'not a bug',
    ]
    label_to_idx = {label: i for i, label in enumerate(all_labels)}
    
    # Track statistics for all bug types
    bug_stats = {}
    for label in all_labels:
        bug_stats[label] = {
            'true_positive': [],   # Correctly predicted this bug type
            'true_negative': [],   # Correctly predicted NOT this bug type
            'false_positive': [],  # Incorrectly predicted this bug type
            'false_negative': [],  # Missed this bug type
        }

    # Iterate through all leaf dirs with both bug and fix files

    total_labels = 0
    total_runs = 0
    not_a_bug_tests=0
    for dirpath, bug_files, fix_files in find_leaf_dirs_with_bug_fix(test_base_dir):
        true_label = []
        # read ground-truth label
        label_file = os.path.join(dirpath, 'label.txt')
        if not os.path.isfile(label_file):
            print(f"Skipping {dirpath}: no label.txt")
            continue
        with open(label_file, 'r') as lf:
            true_label.extend(line.strip() for line in lf)
        
        if len(true_label) == 1 and true_label[0] == 'not a bug':
            not_a_bug_tests+=1
        else:
            total_labels += len(true_label)
        total_runs += 1
        
        lbl+=1
        lbled.append(dirpath)

        buggy_path = os.path.join(dirpath, bug_files[0])
        fixed_path = os.path.join(dirpath, fix_files[0])

        try:
            with open(buggy_path, 'r') as fb, open(fixed_path, 'r') as ff:
                buggy_code = fb.read()
                fixed_code = ff.read()

            buggy_code = remove_comments(buggy_code)
            fixed_code = remove_comments(fixed_code)

            test = CodeProcessor(buggy_code, fixed_code)
            # Initialize BugInvestigator
            bug_investigator = BugInvestigator("BugDetectors/config.json")
            bug_investigator.build_class_hierarchy()

            bugErrorMessage = bug_investigator.detect_pattern(test)
            pred_label = infer_label(bugErrorMessage)

            # Track statistics for all bug types
            for label in all_labels:
                in_pred = label in pred_label
                in_true = label in true_label
                
                if in_pred and in_true:
                    bug_stats[label]['true_positive'].append(dirpath)
                elif in_pred and not in_true:
                    bug_stats[label]['false_positive'].append(dirpath)
                elif not in_pred and in_true:
                    bug_stats[label]['false_negative'].append(dirpath)
                elif not in_pred and not in_true:
                    bug_stats[label]['true_negative'].append(dirpath)

            mlb = MultiLabelBinarizer()
            mlb.fit(true_label + pred_label)

            print(f"Dir: {dirpath}")
            print(f"  True Label: {true_label}")
            print(f"  Pred Label: {pred_label}")
            print('\n\n')

            y_true.append(true_label)
            y_pred.append(pred_label) 

            true_bin = [encode_labels(true_label, label_to_idx)]
            pred_bin = [encode_labels(pred_label, label_to_idx)]

            num = 0
            den = 0

            for actual_label, predicted_label in zip(true_bin[0], pred_bin[0]):
                if actual_label == predicted_label and actual_label != 0:
                    num += 1
                    den += 1
                elif actual_label != predicted_label:
                    den += 1
            
            accuracy = num / den if den > 0 else 0
            if accuracy==1:
                crt+=1
                working.append(dirpath)
            else:
                fail+=1
                failed.append(dirpath)

            precision = precision_score(true_bin, pred_bin, average='micro')
            recall = recall_score(true_bin, pred_bin, average='micro')

            accuracy_array.append(accuracy)
            precision_array.append(precision)
            recall_array.append(recall)

        except Exception:
            print(f"ERROR AT {dirpath}")
            traceback.print_exc()
            amt+=1
            curr.append(dirpath)

    if(accuracy_array):
        accuracy_array = np.array(accuracy_array)
        recall_array = np.array(recall_array)
        precision_array = np.array(precision_array)
        print("\n" + "="*80)
        print("OVERALL METRICS")
        print("="*80)
        print(f"Average Accuracy:  {np.mean(accuracy_array):.4f}")
        print(f"Average Recall:    {np.mean(recall_array):.4f}")
        print(f"Average Precision: {np.mean(precision_array):.4f}")

        print("\n\nAverage Accuracy = ", np.mean(accuracy_array))
        print("Average Recall = ", np.mean(recall_array))
        print("Average Precision = ", np.mean(precision_array))
        print('Labeled Testcases: ', lbl)
        print('Crashing Testcases: ', amt)
        print('Failed Testcases: ', fail)
        print('Working Testcases: ', crt)
        print("Crashing: ",curr)
        print("Failed: ",failed)
        
        # Print statistics per bug fix pattern
        print("\n" + "="*80)
        print("STATISTICS PER BUG FIX PATTERN")
        print("="*80)
        for label in all_labels:
            tp_count = len(bug_stats[label]['true_positive'])
            tn_count = len(bug_stats[label]['true_negative'])
            fp_count = len(bug_stats[label]['false_positive'])
            fn_count = len(bug_stats[label]['false_negative'])
            
            print(f"\n{label}:")
            print(f"  True Positives (TP):  {tp_count}")
            print(f"  True Negatives (TN):  {tn_count}")
            print(f"  False Positives (FP): {fp_count}")
            print(f"  False Negatives (FN): {fn_count}")
            
            # Calculate precision, recall, and F1-score for this pattern
            precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
            recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            accuracy = (tp_count + tn_count) / (tp_count + tn_count + fp_count + fn_count) if (tp_count + tn_count + fp_count + fn_count) > 0 else 0
            
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall:    {recall:.4f}")
            print(f"  F1-Score:  {f1:.4f}")
            print(f"  Accuracy:  {accuracy:.4f}")

    print("\n" + "="*80)
    print("CRASHING TESTCASES")
    print("="*80)
    if curr:
        for path in curr:
            print(path)
    else:
        print("None")

    print("\n" + "="*80)
    print("FAILED TESTCASES")
    print("="*80)
    if failed:
        for path in failed:
            print(path)
    else:
        print("None")

    print(f"Average Bugs per testcase: {total_labels/(total_runs - not_a_bug_tests)}")
    print(f"Total number of testcases: {total_runs}")
    print(f"Total number of labels: {total_labels}")
    print(f"Total number of not a bugs: {not_a_bug_tests}")

if __name__ == "__main__":
    main()