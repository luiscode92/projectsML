<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 p-6 bg-white rounded-md shadow">
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
        Upload a Video
      </h2>
      <div class="rounded-md shadow-sm -space-y-px">
        <div>
          <label class="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
            <span>Select a video</span>
            <input type="file" @change="onFileChange" accept="video/*" class="sr-only">
          </label>
        </div>
        <div>
          <button @click="uploadVideo" class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            Upload
          </button>
        </div>
        <div v-if="processedFile">
          <a :href="processedFile" download class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
            Download Processed Video
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedFile: null,
      processedFile: null,
    };
  },
  methods: {
    onFileChange(e) {
      this.selectedFile = e.target.files[0];
    },
    async uploadVideo() {
      if (!this.selectedFile) {
        alert("Please select a file first!");
        return;
      }
      
      const formData = new FormData();
      formData.append("file", this.selectedFile);

      try {
        const response = await fetch("http://localhost:8000/upload/", {
          method: "POST",
          body: formData,
        });
        const data = await response.json();
        console.log(data);

        // process the uploaded video
        await this.processVideo(data.filename);
      } catch (error) {
        console.error("An error occurred:", error);
      }
    },
    async processVideo(filename) {
      const silent_threshold = 0.3;  // change this as needed

      try {
        const response = await fetch(`http://localhost:8000/process_video/${filename}?silent_threshold=${silent_threshold}`);
        const data = await response.json();

        this.processedFile = `http://localhost:8000/${data.output_file}`;
      } catch (error) {
        console.error("An error occurred:", error);
      }
    },
  },
};
</script>
