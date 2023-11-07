
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from PIL import Image

import numpy as np


def calculate_closest_dimensions(input_width, input_length):
    print("HERE")
    print(input_width,input_length)
    # Define possible section sizes in vertices
    section_sizes_vertices = [7, 15, 31, 63, 127, 255]
    sections_per_component = [1]

 

    # Iterate over possible section sizes in quads
    for vertice_size in section_sizes_vertices:
        for section in sections_per_component:
            # Calculate the number of components needed based on the input dimensions
            component_size = vertice_size * section
            num_components_width = -(-input_width // component_size)  # This is a "ceiling" division
            num_components_length = -(-input_length // component_size)
            
            if num_components_length <= 32 and num_components_width <= 32:
                # Calculate the overall resolution in vertices
                overall_resolution_width = num_components_width * component_size + 1
                overall_resolution_length = num_components_length * component_size + 1

                # If the calculated resolution meets the criteria, return it
                if overall_resolution_width >= input_width and overall_resolution_length >= input_length:
                    print(f"Section Size: {vertice_size}x{vertice_size} (vertices)")
                    print(f"Sections Per Component: {section}x{section}")
                    print(f"Number of Components: {num_components_width}x{num_components_length}")
                    print(f"Overall Resolution: {overall_resolution_width}x{overall_resolution_length} (vertices)")
                    return overall_resolution_width, overall_resolution_length

    print("Unable to find a valid configuration for the given dimensions.")
    return None, None







def resample_band_data(band_data, new_width, new_height):
    padded = np.full((new_height, new_width), 0, dtype=band_data.dtype)  # Use 0 for padding
    padded[:band_data.shape[0], :band_data.shape[1]] = band_data
    return padded


def convert_image_band(img_data, output_filename, new_width, new_height):
    img_data = np.array(img_data)

    if len(img_data.shape) > 2:
        img_data = np.mean(img_data, axis=2)

    img_data = np.where(img_data < 0, 0, img_data)

    

    # Now pad the data before normalization
    img_data_padded = resample_band_data(img_data, new_width, new_height)

   # Separate actual data from sentinel values
    actual_data = np.where(img_data_padded != 0, img_data_padded, 0)  # Check for 0 as padding


# Flatten the array and find unique elements
    unique_values = np.unique(actual_data.ravel())

# Sort the unique values
    sorted_unique_values = np.sort(unique_values)

# Extract the minimum and second minimum
    min_val = sorted_unique_values[0]
    second_min_val = sorted_unique_values[1] if len(sorted_unique_values) > 1 else None
    third_min_val = sorted_unique_values[2] if len(sorted_unique_values) > 2 else None


# Print the range of the data BEFORE normalization to 16-bit integer
    print("Before Normalization Minimum Value:", min_val)
    print("Before Normalization Second Minimum Value:", second_min_val)
    print("Before Normalization THIRD Minimum Value:", third_min_val)

    print("Before Normalization Maximum Value:", actual_data.max())


    # Normalize only the actual data
    min_val = actual_data.min()
    range_val = actual_data.max() - second_min_val
    normalized_data = ((actual_data - second_min_val) / range_val * 65534).astype(np.uint16) + 1
    print("Before Padding and Before Conversion Minimum Value:", normalized_data.min())
    print("Before Padding and Before Conversion Maximum Value:", normalized_data.max())

      # Calculate the Z-scale for Unreal Engine
    ue_default_range = 512  # 512 meters (+/- 256m) for 100% Z-scale
    z_scale_percentage = (range_val *100/ ue_default_range)/30
    print(f"Recommended Z Scale in Unreal Engine: {z_scale_percentage:.2f}%")
    # Apply the sentinel value in the 16-bit range
    img_data_16bit = np.where(img_data_padded != 0, normalized_data, 0)  # Using 0 for sentinel in 16-bit

   # Flatten the array and find unique elements
    unique_values = np.unique(img_data_16bit.ravel())

    # Sort the unique values
    sorted_unique_values = np.sort(unique_values)

    # Extract the minimum and second minimum
    min_val = sorted_unique_values[0]
    second_min_val = sorted_unique_values[1] if len(sorted_unique_values) > 1 else None
    third_min_val = sorted_unique_values[2] if len(sorted_unique_values) > 2 else None


# Print Min/Max before padding
    print("After Padding and Before Conversion Minimum Value:", min_val)
    print("After Padding and Before Conversion Second Minimum Value:", second_min_val)

    print("After Padding and Before Conversion THIRD Minimum Value:", third_min_val)

    print("After Padding and Before Conversion Maximum Value:", img_data_16bit.max())


    # Now you can continue with the rest of the processing
    img_16bit = Image.fromarray(img_data_16bit)
    img_16bit.save(output_filename, format="PNG")


def process_geotiff(filename):
    with rasterio.open(filename) as src:
        print(f"Original dimensions of {filename}: Width = {src.width}, Height = {src.height}")
        
        new_width, new_height = calculate_closest_dimensions(src.width, src.height)
        print(new_width,new_height)
        
        for band_index in range(1, src.count + 1):
            band_data = src.read(band_index).squeeze()

            output_filename = filename[:-4] + "ASDFDF" + str(band_index) + ".png"
            convert_image_band(band_data, output_filename, new_width, new_height)

input_path = "C:\\Users\\hanna\\OneDrive\\Desktop\\Data_to_use\\Bob_Marshall\\LCG_LF2022_FBFM40_230_CONUS\\LCG_LC22_F40_230.tif"
process_geotiff(input_path)
print("OK")
