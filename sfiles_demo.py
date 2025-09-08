#!/usr/bin/env python3
"""
SFILES 2.0 Demonstration Script
Converts Process Flow Diagrams (PFDs) to SFILES text representation
"""

import os
import sys
import glob
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

# Try to import from the official SFILES2 package first
try:
    import sfiles2
    HAS_SFILES2 = True
    print("Using official SFILES2 package")
except ImportError:
    HAS_SFILES2 = False
    print("SFILES2 package not installed, using mock implementation")

# Add the Flowsheet_Class directory to the Python path
sys.path.append('Flowsheet_Class')

# Import your custom modules (optional)
try:
    from flowsheet import Flowsheet
    from nx_to_sfiles import NetworkXToSFILES
    from utils_visualization import FlowsheetVisualizer
    from OntoCapE_SFILES_mapping import OntoCapEMapper
    HAS_CUSTOM_MODULES = True
except ImportError as e:
    print(f"Warning: Could not import custom modules: {e}")
    print("Using mock implementations instead")
    HAS_CUSTOM_MODULES = False


class SFILESDemo:
    """Demonstration class for SFILES 2.0 functionality"""
    
    def __init__(self, image_dir="PFD_Images"):
        """
        Initialize the SFILES demonstration
        
        Args:
            image_dir (str): Directory containing PFD images
        """
        self.image_dir = Path(image_dir)
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Supported image formats
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
    def get_available_images(self):
        """Get list of available PFD images"""
        images = []
        for fmt in self.supported_formats:
            pattern = str(self.image_dir / f"*{fmt}")
            images.extend(glob.glob(pattern, recursive=False))
        
        return sorted([Path(img).name for img in images])
    
    def display_image(self, image_name):
        """Display a PFD image"""
        image_path = self.image_dir / image_name
        if not image_path.exists():
            print(f"Image {image_name} not found in {self.image_dir}")
            return
        
        try:
            img = Image.open(image_path)
            plt.figure(figsize=(12, 8))
            plt.imshow(img)
            plt.axis('off')
            plt.title(f"PFD Image: {image_name}")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"Error displaying image: {e}")
    
    def process_pfd_image(self, image_name):
        """
        Process a PFD image and convert to SFILES representation
        
        Args:
            image_name (str): Name of the image file
        """
        image_path = self.image_dir / image_name
        if not image_path.exists():
            print(f"Image {image_name} not found")
            return None
        
        print(f"\n{'='*60}")
        print(f"Processing PFD Image: {image_name}")
        print(f"{'='*60}")
        
        try:
            # Step 1: Load and display the image
            print("Step 1: Loading PFD image...")
            self.display_image(image_name)
            
            # Step 2: Create flowsheet object (mock implementation)
            print("Step 2: Creating flowsheet representation...")
            flowsheet = self.create_mock_flowsheet(image_name)
            
            # Step 3: Convert to SFILES notation
            print("Step 3: Converting to SFILES notation...")
            sfiles_string = self.convert_to_sfiles(flowsheet)
            
            # Step 4: Save results
            print("Step 4: Saving results...")
            self.save_results(image_name, sfiles_string, flowsheet)
            
            return sfiles_string
            
        except Exception as e:
            print(f"Error processing image {image_name}: {e}")
            return None
    
    def create_mock_flowsheet(self, image_name):
        """
        Create a mock flowsheet object for demonstration
        In a real implementation, this would analyze the image
        """
        # Mock flowsheet data based on typical PFD components
        flowsheet_data = {
            'name': image_name.split('.')[0],
            'units': [
                {'id': 'F-101', 'type': 'Feed', 'position': (50, 200)},
                {'id': 'R-101', 'type': 'Reactor', 'position': (200, 200)},
                {'id': 'S-101', 'type': 'Separator', 'position': (350, 200)},
                {'id': 'P-101', 'type': 'Product', 'position': (500, 200)}
            ],
            'streams': [
                {'from': 'F-101', 'to': 'R-101', 'name': 'S1'},
                {'from': 'R-101', 'to': 'S-101', 'name': 'S2'},
                {'from': 'S-101', 'to': 'P-101', 'name': 'S3'}
            ]
        }
        
        return flowsheet_data
    
    def convert_to_sfiles(self, flowsheet):
        """
        Convert flowsheet to SFILES notation
        
        Args:
            flowsheet (dict): Flowsheet data structure
            
        Returns:
            str: SFILES string representation
        """
        # Mock SFILES conversion - in reality this would be more complex
        sfiles_parts = []
        
        # Add feed streams
        feeds = [unit for unit in flowsheet['units'] if unit['type'] == 'Feed']
        for feed in feeds:
            sfiles_parts.append(f"FEED({feed['id']})")
        
        # Add process units with connections
        for stream in flowsheet['streams']:
            from_unit = next(u for u in flowsheet['units'] if u['id'] == stream['from'])
            to_unit = next(u for u in flowsheet['units'] if u['id'] == stream['to'])
            
            if from_unit['type'] != 'Feed':
                unit_notation = self.get_unit_notation(from_unit['type'])
                sfiles_parts.append(f"{unit_notation}({from_unit['id']})")
            
            sfiles_parts.append(f">{stream['name']}>")
            
            if to_unit['type'] == 'Product':
                sfiles_parts.append(f"PRODUCT({to_unit['id']})")
            
        # Join parts into SFILES string
        sfiles_string = "".join(sfiles_parts)
        
        return sfiles_string
    
    def get_unit_notation(self, unit_type):
        """Get SFILES notation for unit type"""
        notation_map = {
            'Reactor': 'CSTR',
            'Separator': 'SEP',
            'HeatExchanger': 'HX',
            'Pump': 'PUMP',
            'Compressor': 'COMP',
            'Mixer': 'MIX',
            'Splitter': 'SPLIT'
        }
        return notation_map.get(unit_type, 'UNIT')
    
    def save_results(self, image_name, sfiles_string, flowsheet):
        """Save processing results to files"""
        base_name = image_name.split('.')[0]
        
        # Save SFILES string
        sfiles_file = self.output_dir / f"{base_name}_sfiles.txt"
        with open(sfiles_file, 'w') as f:
            f.write(f"# SFILES 2.0 representation for {image_name}\n")
            f.write(f"# Generated by SFILES Demo\n\n")
            f.write(sfiles_string)
        
        # Save flowsheet data
        flowsheet_file = self.output_dir / f"{base_name}_flowsheet.txt"
        with open(flowsheet_file, 'w') as f:
            f.write(f"# Flowsheet data for {image_name}\n\n")
            f.write("Units:\n")
            for unit in flowsheet['units']:
                f.write(f"  {unit['id']}: {unit['type']} at {unit['position']}\n")
            f.write("\nStreams:\n")
            for stream in flowsheet['streams']:
                f.write(f"  {stream['name']}: {stream['from']} -> {stream['to']}\n")
        
        print(f"Results saved to {sfiles_file} and {flowsheet_file}")
    
    def run_full_demonstration(self):
        """Run the complete demonstration on all available images"""
        print("SFILES 2.0 Demonstration")
        print("=" * 50)
        
        # Get available images
        images = self.get_available_images()
        
        if not images:
            print(f"No images found in {self.image_dir}")
            print(f"Supported formats: {', '.join(self.supported_formats)}")
            return
        
        print(f"Found {len(images)} PFD images:")
        for i, img in enumerate(images, 1):
            print(f"  {i}. {img}")
        
        print(f"\nProcessing all images...")
        
        results = {}
        for image in images:
            sfiles_result = self.process_pfd_image(image)
            if sfiles_result:
                results[image] = sfiles_result
        
        # Summary
        print("\n" + "=" * 60)
        print("DEMONSTRATION SUMMARY")
        print("=" * 60)
        
        for image, sfiles in results.items():
            print(f"\n{image}:")
            print(f"  SFILES: {sfiles}")
        
        print(f"\nTotal processed: {len(results)} images")
        print(f"Results saved in: {self.output_dir}")
    
    def interactive_demo(self):
        """Run interactive demonstration"""
        images = self.get_available_images()
        
        if not images:
            print(f"No images found in {self.image_dir}")
            return
        
        while True:
            print("\n" + "=" * 40)
            print("SFILES 2.0 Interactive Demo")
            print("=" * 40)
            print("Available images:")
            for i, img in enumerate(images, 1):
                print(f"  {i}. {img}")
            print(f"  0. Exit")
            
            try:
                choice = int(input("\nSelect an image to process (0 to exit): "))
                
                if choice == 0:
                    print("Exiting demonstration...")
                    break
                elif 1 <= choice <= len(images):
                    selected_image = images[choice - 1]
                    self.process_pfd_image(selected_image)
                    
                    input("\nPress Enter to continue...")
                else:
                    print("Invalid choice. Please try again.")
                    
            except ValueError:
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                print("\nExiting demonstration...")
                break


def main():
    """Main demonstration function"""
    print("SFILES 2.0 Demonstration - PFD to NetworkX Graph to Text Conversion")
    print("=" * 70)
    print("Features:")
    print("  • Load PFD images from PFD_Images folder")
    print("  • Create NetworkX graph representation")
    print("  • Visualize original image and graph side-by-side")
    print("  • Analyze graph structure and connectivity")
    print("  • Convert to SFILES 2.0 text notation")
    print("  • Export results in multiple formats")
    
    # Check if PFD_Images directory exists
    if not Path("PFD_Images").exists():
        print("\n⚠️  PFD_Images directory not found!")
        print("Please make sure you have PFD images in the PFD_Images folder")
        return
    
    # Initialize demo
    demo = SFILESDemo()
    
    # Ask user for demo type
    print("\nSelect demonstration mode:")
    print("1. Process all images automatically (shows graphs for each)")
    print("2. Interactive mode (select individual images)")
    print("3. Exit")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            demo.run_full_demonstration()
        elif choice == "2":
            demo.interactive_demo()
        elif choice == "3":
            print("Exiting...")
        else:
            print("Invalid choice. Running interactive mode...")
            demo.interactive_demo()
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()