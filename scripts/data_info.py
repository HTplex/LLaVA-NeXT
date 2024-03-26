import json
import os
from PIL import Image
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np


def load_data(json_path):
    with open(json_path, "r") as f:
        return json.load(f)


def filter_data(data):
    # filtered_data = [item for item in data if "image" in item and "text" in item["image"]]
    filtered_data = [item for item in data if "image" in item]
    return filtered_data


from multiprocessing import Pool
import functools


def calculate_image_dimension(item, images_folder):
    image_path = os.path.join(images_folder, item["image"])
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return width, height
    except Exception as e:
        print(f"Error opening {image_path}: {e}")
        return None, None


def calculate_image_dimensions_multiprocess(filtered_data, images_folder, num_processes=96):
    with Pool(num_processes) as p:
        dimensions = list(tqdm(p.imap(functools.partial(calculate_image_dimension, images_folder=images_folder), filtered_data), total=len(filtered_data), desc="Calculating image dimensions"))
    widths, heights = zip(*[dim for dim in dimensions if dim[0] is not None])
    return list(widths), list(heights)


def plot_histogram(data, title, xlabel, ylabel, bins_width=10):
    hist, bin_edges = np.histogram(data, bins=np.arange(0, max(data) + bins_width, bins_width))
    bins = np.arange(0, max(data) + 10, 10)  # Adjust the bin width as needed
    plt.figure(figsize=(12, 6))
    plt.bar(bin_edges[:-1], hist, width=bins_width - 1, edgecolor="black", log=True)
    plt.xticks(np.arange(min(bins), max(bins) + 1, bins_width), rotation=90)
    plt.xlim(min(bin_edges), max(bin_edges))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title, fontsize=8)
    plt.savefig(f"./{title}.png")
    # plt.show()


def plot_2d_histogram(widths, heights, title, xlabel, ylabel, bins_size=(500, 500)):  # Increased bin size
    plt.figure(figsize=(12, 12))
    h, xedges, yedges, image = plt.hist2d(widths, heights, bins=[np.arange(min(widths), max(widths) + bins_size[0], bins_size[0]), np.arange(min(heights), max(heights) + bins_size[1], bins_size[1])], cmap=plt.cm.jet, density=True)
    plt.colorbar()
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title + "\n" + f"Max width: {max(widths)}, Max height: {max(heights)}", fontsize=10)
    plt.savefig(f"./{title}.png")


def tokenize(text):
    return text.split()


def calculate_tokenized_lengths(data):
    lengths = []
    for item in tqdm(data, desc="Tokenizing conversations"):
        for conversation in item["conversations"]:
            tokenized_value = tokenize(conversation["value"])
            lengths.append(len(tokenized_value))
    return lengths


import argparse
def main():
    parser = argparse.ArgumentParser(description="Process data for LLaVA_Next project.")
    parser.add_argument("--json_path", type=str, help="Path to the JSON file containing data.")
    parser.add_argument("--images_folder", type=str, help="Path to the folder containing images.")
    args = parser.parse_args()

    llava_instruct_name = args.json_path.split('/')[-1].replace('.json', '')
    json_path = args.json_path
    # llava_instruct_name = "textcaps_train"
    # json_path = f"/mnt/bn/vl-research/data/llava_instruct/{llava_instruct_name}.json"
    llava_instruct_name = os.path.basename(json_path).replace(".json", "")
    # images_folder = "/mnt/bn/vl-research/data/llava_data"
    images_folder = args.images_folder

    data = load_data(json_path)
    filtered_data = filter_data(data)

    print(f"Total data items: {len(data)}, Filtered data items: {len(filtered_data)}")
    widths, heights = calculate_image_dimensions_multiprocess(filtered_data, images_folder)
    max_diwth = max(widths)
    max_height = max(heights)
    print(f"Max width: {max_diwth}, Max height: {max_height}")
    plot_2d_histogram(widths, heights, f"dist_{llava_instruct_name}_2d_w_h", "Width", "Height", bins_size=(100, 100))

    tokenized_lengths = calculate_tokenized_lengths(filtered_data)
    plot_histogram(tokenized_lengths, f"dist_{llava_instruct_name}_tokenized_length", "Tokenized Length", "Count (log scale)", bins_width=10)


if __name__ == "__main__":
    main()