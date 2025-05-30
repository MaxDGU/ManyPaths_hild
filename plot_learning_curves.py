import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Define a consistent style
sns.set_theme(style="whitegrid")

# --- Placeholder Data Generation ---
def generate_dummy_maml_trajectory(epochs=100, log_interval=10):
    """Generates a dummy MAML trajectory DataFrame."""
    steps = np.arange(log_interval, epochs + 1, log_interval)
    dummy_data = {
        'log_step': steps, # Corresponds to 'episodes_seen' / LOG_INTERVAL usually
        'val_loss': 0.7 - 0.3 * (1 - np.exp(-steps / (epochs * 0.3))) + np.random.normal(0, 0.02, len(steps)),
        'val_accuracy': 0.5 + 0.4 * (1 - np.exp(-steps / (epochs * 0.4))) + np.random.normal(0, 0.02, len(steps)),
        'grad_alignment': 0.1 + 0.6 * (1 - np.exp(-steps / (epochs * 0.5))) + np.random.normal(0, 0.05, len(steps))
    }
    df = pd.DataFrame(dummy_data)
    # Clip accuracy to be between 0 and 1
    df['val_accuracy'] = df['val_accuracy'].clip(0, 1)
    return df

def generate_dummy_sgd_trajectory(num_tasks=200):
    """Generates a dummy SGD baseline trajectory DataFrame."""
    dummy_data = {
        'task_idx': np.arange(num_tasks),
        'query_loss': 0.6 - 0.2 * (1 - np.exp(-np.arange(num_tasks) / (num_tasks * 0.5))) + np.random.normal(0, 0.03, num_tasks),
        'query_accuracy': 0.55 + 0.3 * (1 - np.exp(-np.arange(num_tasks) / (num_tasks * 0.6))) + np.random.normal(0, 0.03, num_tasks),
        'final_support_loss': np.random.rand(num_tasks) * 0.1,
        'num_sgd_steps': [100] * num_tasks,
        'lr': [1e-3] * num_tasks
    }
    df = pd.DataFrame(dummy_data)
    df['query_accuracy'] = df['query_accuracy'].clip(0, 1)
    return df

def generate_dummy_drift_data(num_points=100, type='maml', final_drift_mean=5.0, final_drift_std=1.0):
    """Generates dummy weight drift data."""
    if type == 'maml':
        epochs = np.arange(1, num_points + 1) * 100 # Assuming 100 is a log interval
        drift_from_init = final_drift_mean * (1 - np.exp(-epochs / (num_points * 100 * 0.4))) + np.random.normal(0, 0.1, num_points)
        drift_from_prev = np.abs(np.random.normal(0.1, 0.05, num_points) * (final_drift_mean / epochs[-1]) * (epochs[-1] - epochs/2) / (epochs[-1]/2) ) # smaller drifts from prev
        df = pd.DataFrame({
            'epoch': epochs,
            'l2_drift_from_init': drift_from_init,
            'l2_drift_from_previous': drift_from_prev
        })
        return df
    elif type == 'sgd': # Represents final drift of N independent SGD models from their inits
        drifts = np.random.normal(loc=final_drift_mean * 0.8, scale=final_drift_std, size=num_points) # SGD might drift less or more variably
        df = pd.DataFrame({
            'final_l2_drift_from_init': np.abs(drifts) # Ensure positive
        })
        return df
    return pd.DataFrame()

# --- Plotting Functions ---

def plot_maml_learning_curves(df_maml, title_suffix="", output_dir="figures"):
    """Plots MAML validation loss, accuracy, and grad alignment."""
    if df_maml.empty:
        print(f"MAML dataframe is empty for {title_suffix}. Skipping plot.")
        return

    fig, axs = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    
    # Convert log_step to epochs (assuming log_step is episode count and LOG_INTERVAL from constants.py is 1000)
    # This might need adjustment based on actual CSV structure. For dummy data, 'log_step' is already 'epoch-like'.
    # If 'log_step' in real data is truly 'episodes_seen', you'd divide by tasks_per_log_interval (e.g., 1000)
    # For now, let's assume df_maml['log_step'] can be directly used as x-axis for epochs for simplicity with dummy.
    epochs_col = 'log_step' 

    # Val Loss
    sns.lineplot(ax=axs[0], x=epochs_col, y='val_loss', data=df_maml, label="Meta-Validation Loss", color='royalblue')
    axs[0].set_ylabel("Loss")
    axs[0].set_title(f"MAML Meta-Validation Loss {title_suffix}")
    axs[0].legend()

    # Val Accuracy
    sns.lineplot(ax=axs[1], x=epochs_col, y='val_accuracy', data=df_maml, label="Meta-Validation Accuracy", color='forestgreen')
    axs[1].set_ylabel("Accuracy")
    axs[1].set_title(f"MAML Meta-Validation Accuracy {title_suffix}")
    axs[1].legend()
    axs[1].set_ylim(0, 1.05)

    # Grad Alignment
    if 'grad_alignment' in df_maml.columns:
        sns.lineplot(ax=axs[2], x=epochs_col, y='grad_alignment', data=df_maml, label="Gradient Alignment", color='purple')
        axs[2].set_ylabel("Cosine Similarity")
        axs[2].set_title(f"MAML Gradient Alignment {title_suffix}")
        axs[2].legend()
        # axs[2].set_ylim(-1.05, 1.05) # Optional: if alignment is always in [-1, 1]

    axs[2].set_xlabel("Training Steps / Epochs")
    
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, f"maml_learning_curves{title_suffix.replace(' ', '_')}.png"))
    print(f"Saved MAML learning curves plot to {output_dir}/")
    plt.close(fig)

def plot_sgd_performance_distribution(df_sgd, title_suffix="", output_dir="figures"):
    """Plots distribution of SGD query accuracy and loss over tasks."""
    if df_sgd.empty:
        print(f"SGD dataframe is empty for {title_suffix}. Skipping plot.")
        return

    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    sns.histplot(ax=axs[0], data=df_sgd, x='query_accuracy', kde=True, color='coral')
    axs[0].set_title(f"SGD Query Accuracy Distribution {title_suffix}")
    axs[0].set_xlabel("Query Accuracy")
    axs[0].set_xlim(0,1.05)

    sns.histplot(ax=axs[1], data=df_sgd, x='query_loss', kde=True, color='skyblue')
    axs[1].set_title(f"SGD Query Loss Distribution {title_suffix}")
    axs[1].set_xlabel("Query Loss")

    plt.suptitle(f"SGD Baseline Performance Over {len(df_sgd)} Tasks {title_suffix}", y=1.02)
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, f"sgd_performance_distribution{title_suffix.replace(' ', '_')}.png"))
    print(f"Saved SGD performance distribution plot to {output_dir}/")
    plt.close(fig)

def plot_gradient_alignment_maml(df_maml, title_suffix="", output_dir="figures"):
    """Plots MAML gradient alignment specifically."""
    if df_maml.empty or 'grad_alignment' not in df_maml.columns:
        print(f"MAML dataframe for grad alignment is empty or missing column for {title_suffix}. Skipping plot.")
        return

    fig, ax = plt.subplots(1, 1, figsize=(10, 4))
    epochs_col = 'log_step' # Assuming similar x-axis as other MAML plots

    sns.lineplot(ax=ax, x=epochs_col, y='grad_alignment', data=df_maml, label="Gradient Alignment", color='purple')
    ax.set_ylabel("Cosine Similarity")
    ax.set_title(f"MAML Gradient Alignment Over Training {title_suffix}")
    ax.set_xlabel("Training Steps / Epochs")
    ax.legend()
    # ax.set_ylim(-1.05, 1.05) # Optional

    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, f"maml_gradient_alignment{title_suffix.replace(' ', '_')}.png"))
    print(f"Saved MAML gradient alignment plot to {output_dir}/")
    plt.close(fig)

def plot_weight_drift_comparison(df_maml_drift, df_sgd_final_drifts, title_suffix="", output_dir="figures"):
    """Plots MAML weight drift over epochs and a distribution of final SGD model drifts."""
    
    fig, axs = plt.subplots(1, 2, figsize=(15, 6))

    # MAML Weight Drift
    if not df_maml_drift.empty and 'l2_drift_from_init' in df_maml_drift.columns:
        sns.lineplot(ax=axs[0], x='epoch', y='l2_drift_from_init', data=df_maml_drift, label="MAML: Drift from Init", color='darkorange')
        if 'l2_drift_from_previous' in df_maml_drift.columns:
             sns.lineplot(ax=axs[0], x='epoch', y='l2_drift_from_previous', data=df_maml_drift, label="MAML: Drift from Prev Checkpoint", color='gold', linestyle='--')
        axs[0].set_xlabel("MAML Training Epochs")
        axs[0].set_ylabel("L2 Distance (Parameters)")
        axs[0].set_title(f"MAML Weight Drift {title_suffix}")
        axs[0].legend()
    else:
        axs[0].text(0.5, 0.5, "MAML drift data missing or incomplete", ha='center', va='center')
        axs[0].set_title(f"MAML Weight Drift {title_suffix}")

    # SGD Final Weight Drift Distribution
    if not df_sgd_final_drifts.empty and 'final_l2_drift_from_init' in df_sgd_final_drifts.columns:
        sns.histplot(ax=axs[1], data=df_sgd_final_drifts, x='final_l2_drift_from_init', kde=True, color='teal', bins=20)
        axs[1].set_xlabel("L2 Distance (Final SGD Model from its Init)")
        axs[1].set_ylabel("Number of SGD Tasks")
        axs[1].set_title(f"Distribution of Final SGD Model Drifts {title_suffix}")
    else:
        axs[1].text(0.5, 0.5, "SGD drift data missing or incomplete", ha='center', va='center')
        axs[1].set_title(f"Distribution of Final SGD Model Drifts {title_suffix}")

    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, f"weight_drift_comparison{title_suffix.replace(' ', '_')}.png"))
    print(f"Saved weight drift comparison plot to {output_dir}/")
    plt.close(fig)


# --- Main section to generate plots with dummy data ---
if __name__ == "__main__":
    print("Generating plots with dummy data...")

    # Create dummy dataframes
    dummy_maml_df_simple = generate_dummy_maml_trajectory(epochs=10000, log_interval=100) # 100 points
    dummy_maml_df_complex = generate_dummy_maml_trajectory(epochs=10000, log_interval=100) 
    # Make complex one learn a bit slower and less perfectly
    dummy_maml_df_complex['val_accuracy'] *= 0.9 
    dummy_maml_df_complex['val_accuracy'] -= 0.05
    dummy_maml_df_complex['val_accuracy'] = dummy_maml_df_complex['val_accuracy'].clip(0,1)
    dummy_maml_df_complex['grad_alignment'] *= 0.85


    dummy_sgd_df_simple = generate_dummy_sgd_trajectory(num_tasks=200)
    dummy_sgd_df_complex = generate_dummy_sgd_trajectory(num_tasks=200)
    dummy_sgd_df_complex['query_accuracy'] *= 0.88
    dummy_sgd_df_complex['query_accuracy'] -= 0.08
    dummy_sgd_df_complex['query_accuracy'] = dummy_sgd_df_complex['query_accuracy'].clip(0,1)

    # Generate dummy drift data
    dummy_maml_drift_simple = generate_dummy_drift_data(num_points=100, type='maml', final_drift_mean=10)
    dummy_sgd_final_drifts_simple = generate_dummy_drift_data(num_points=200, type='sgd', final_drift_mean=8, final_drift_std=2.0)
    
    dummy_maml_drift_complex = generate_dummy_drift_data(num_points=100, type='maml', final_drift_mean=15)
    dummy_sgd_final_drifts_complex = generate_dummy_drift_data(num_points=200, type='sgd', final_drift_mean=12, final_drift_std=2.5)

    # Plot for a 'simple' concept setting
    plot_maml_learning_curves(dummy_maml_df_simple, title_suffix=" (Concept: Simple)")
    plot_sgd_performance_distribution(dummy_sgd_df_simple, title_suffix=" (Concept: Simple)")
    plot_gradient_alignment_maml(dummy_maml_df_simple, title_suffix=" (Concept: Simple)")
    plot_weight_drift_comparison(dummy_maml_drift_simple, dummy_sgd_final_drifts_simple, title_suffix=" (Concept: Simple)")

    # Plot for a 'complex' concept setting
    plot_maml_learning_curves(dummy_maml_df_complex, title_suffix=" (Concept: Complex)")
    plot_sgd_performance_distribution(dummy_sgd_df_complex, title_suffix=" (Concept: Complex)")
    plot_gradient_alignment_maml(dummy_maml_df_complex, title_suffix=" (Concept: Complex)")
    plot_weight_drift_comparison(dummy_maml_drift_complex, dummy_sgd_final_drifts_complex, title_suffix=" (Concept: Complex)")
    
    print("Finished generating dummy plots. Check the 'figures' directory.")

    # TODO:
    # 1. Create functions to load REAL trajectory CSVs for MAML and SGD.
    #    - These functions should parse filenames to get parameters (features, depth, seed, etc.).
    #    - They should handle multiple seeds and potentially average them or plot with confidence intervals.
    # 2. Integrate these loading functions into the main section.
    # 3. Refine x-axis for MAML plots if 'log_step' is not directly 'epochs'.
    #    (e.g., if log_step is #episodes, and main.py's LOG_INTERVAL for saving trajectory is, say, 1000 episodes)
    #    The current dummy data uses 'log_step' more like a direct epoch counter.
    #    Real MAML trajectory CSVs have 'log_step' which means "every X episodes" where X is the meta_train LOG_INTERVAL.
    #    So, the x-axis label might be "Logging Steps (x LOG_INTERVAL episodes_seen)".
    # 4. Add comparison plots (MAML vs SGD final performance). 
    # 5. Create functions to load REAL drift data (from analyze_checkpoint_drift.py output for MAML, 
    #    and potentially calculated from saved SGD models for SGD final drifts).