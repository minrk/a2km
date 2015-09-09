# Copyright Min RK, License: BSD 3-clause

require 'json'

module A2KM

  def initialize
    @kernels = nil
  end

  def A2KM.kernels
    if @kernels.nil?
      js = JSON.parse `jupyter kernelspec list --json`
      @kernels = js['kernelspecs']
    end
    @kernels
  end

  def A2KM.kernel_dirs
    paths = JSON.parse `jupyter --paths --json`
    paths['data'].map do |p|
      p + '/' + 'kernels'
    end
  end

  def A2KM.user_kernel_dir
    kernel_dirs.first
  end

  def A2KM.get_kernel(name)
    "Get a kernel by name. Die with message if not found."
    if not kernels.has_key? name
      STDERR.puts "No such kernel: #{name}"
      STDERR.puts "Found kernels: #{kernels.keys.sort.join(' ')}"
      exit(-1)
    end
    kernels[name]
  end

  def A2KM.kernel_json_path(name)
    "Return path to a kernel's kernel.json"
    kernel = get_kernel(name)
    File.join(kernel['resources_dir'], 'kernel.json')
  end

  def A2KM.get_kernel_json(name)
    "Return kernel.json contents for a given kernelspec"
    File.open(kernel_json_path(name)) do |f|
      return JSON.parse f.read
    end
  end

  def A2KM.save_kernel_json(name, data)
    "save new kernel JSON"
    File.open(kernel_json_path(name), 'w') do |f|
      f.write JSON.pretty_generate(data)
    end
  end
end
