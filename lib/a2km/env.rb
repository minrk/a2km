# Copyright Min RK, License: BSD 3-clause

require 'Open3'
require 'liquid'

class ENVError < StandardError
end

module A2KM
  
  module ENV_UTILS

    ACTIVATE_TPL_S = "{{activate}} {{name}}"
    ACTIVATE_TPL = Liquid::Template.parse ACTIVATE_TPL_S
    ENV_CMD_TPL = Liquid::Template.parse(<<-END
#!/usr/bin/env bash
set -e
#{ACTIVATE_TPL_S}
exec python -m ipykernel $@
END
    )

    CONDA_ACTIVATE = 'source activate'
    VIRTUALENV_ACTIVATE = 'workon'
    
    module_function
    
    def activate_cmd(kind)
      case kind
      when 'conda'
        return CONDA_ACTIVATE
      when 'venv'
        return VIRTUALENV_ACTIVATE
      else
        throw ArgumentError, "kind must be 'conda' or 'venv', not '#{kind}'"
      end
    end
  
    def in_env(env, cmd, kind: 'conda')
      Open3::popen2('bash') do |stdin, stdout, wait_thr|
        stdin.puts 'set -e'
        stdin.puts ACTIVATE_TPL.render('name' => env, 'activate' => activate_cmd(kind))
        stdin.puts cmd
        stdin.close
        status = wait_thr.value
        if status != 0
          raise ENVError.new("Failed to run #{cmd} in #{kind} env: #{env}")
        end
        return stdout.read
      end
    end
  
    def kernel_script(name, kind: 'conda')
      # return kernel script as a string
      ENV_CMD_TPL.render('name' => name, 'activate' => activate_cmd(kind))
    end
  
    def ipykernel_version(env, kind: 'conda')
      in_env(env, "python -c 'import ipykernel; print(ipykernel.__version__)'", kind: kind)
    end

    def make_kernel_exe(kernel_name, env_name, kind: 'conda', prefix: '/usr/local')
      cmd = kernel_script(env_name, kind: kind)
      bin = File.join(prefix, 'bin')
      if not File.directory? bin
        FileUtils.mkdir bin
      end
      kernel_exe = File.join(bin, "jupyter-kernel-#{kernel_name}")
      puts "Making executable '#{kernel_exe}'"
      
      File.open(kernel_exe, 'w') do |f|
        f.write(cmd)
      end
      File.chmod(0o755, kernel_exe)
      return kernel_exe
    end
  
    def get_prefix(name, kind)
      in_env(name, 'python -c "import sys; print(sys.prefix)"', kind: kind)
    end
  end

  def self.make_env_kernel(kernel_name, env_name, kind: 'conda', prefix: '/usr/local', user: true)
    prefix = File.expand_path(prefix)
    v = ENV_UTILS.ipykernel_version(env_name, kind: kind)
    
    puts "Found ipykernel-#{v}"
    
    exe = ENV_UTILS.make_kernel_exe(kernel_name, env_name, kind: kind, prefix: prefix)
    if user
      user_arg = '--user'
    else
      user_arg = ''
    end
    
    ENV_UTILS.in_env(env_name, "python -m ipykernel.kernelspec --name #{kernel_name} #{user_arg}", kind: kind)
    spec = A2KM.get_kernel_json(kernel_name)
    spec['argv'] = [exe, '-f', '{connection_file}']
    spec['display_name'] = "#{spec['display_name']} (#{kind}:#{env_name})"
    A2KM.save_kernel_json(kernel_name, spec)
    
  end

end
