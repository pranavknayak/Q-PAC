import os
import traceback
import argparse
from BugInvestigator import BugInvestigator
from CodeProcessor import CodeProcessor
from sklearn.metrics import accuracy_score, precision_score, recall_score

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
    if bugErrorMessage.get('Unitary') and bugErrorMessage['Unitary'] != 'None':
        return 'Operator-related'
    if bugErrorMessage.get('Measurement') and bugErrorMessage['Measurement'] != 'None':
        return 'Measurement-related'
    if bugErrorMessage.get('Initialization') and bugErrorMessage['Initialization'] != 'None':
        return 'Qubit/Initialization-related'
    return 'not a bug'


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

    # Iterate through all leaf dirs with both bug and fix files
    for dirpath, bug_files, fix_files in find_leaf_dirs_with_bug_fix(test_base_dir):
        # read ground-truth label
        label_file = os.path.join(dirpath, 'label.txt')
        if not os.path.isfile(label_file):
            print(f"Skipping {dirpath}: no label.txt")
            continue
        with open(label_file, 'r') as lf:
            true_label = lf.read().strip()

        buggy_path = os.path.join(dirpath, bug_files[0])
        fixed_path = os.path.join(dirpath, fix_files[0])

        try:
            with open(buggy_path, 'r') as fb, open(fixed_path, 'r') as ff:
                buggy_code = fb.read()
                fixed_code = ff.read()

            test = CodeProcessor(buggy_code, fixed_code)
            bugErrorMessage = bug_investigator.detect_pattern(test)
            pred_label = infer_label(bugErrorMessage)

            print(f"Dir: {dirpath}")
            print(f"  True Label: {true_label}")
            print(f"  Pred Label: {pred_label}")

            y_true.append(true_label)
            y_pred.append(pred_label)

        except Exception:
            print(f"ERROR AT {dirpath}")
            traceback.print_exc()

    # Compute and print metrics
    if y_true:
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, average='macro', zero_division=0)
        rec = recall_score(y_true, y_pred, average='macro', zero_division=0)
        print("\nEvaluation Metrics:")
        print(f"  Accuracy: {acc:.4f}")
        print(f"  Precision: {prec:.4f}")
        print(f"  Recall: {rec:.4f}")
    else:
        print("No labeled testcases processed.")

if __name__ == "__main__":
    main()
