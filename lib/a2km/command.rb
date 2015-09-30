# Copyright Min RK, License: BSD 3-clause

require 'json'

require 'rubygems'
require 'commander'
require 'highline'

module A2KM
  
  # Start the a2km entrypoint
  def A2KM.run
    CLI.new.run
  end
  
  # The A2KM CLI entrypoint
  class CLI
    include Commander::Methods
    
    def run
      program :name, 'Assistant to the KernelManager'
      program :version, VERSION
      program :description, 'Work with Jupyter kernelspecs'

      command :rename do |c|
        c.syntax = 'a2km rename <from> <to>'
        c.summary = 'Rename a kernelspec'
        c.description = 'Rename kernelspec FROM to TO'
        c.action do |args, options|
          from = args.shift
          to = args.shift
          kernel = A2KM.get_kernel(from)
          src = kernel['resources_dir']

          dst = File.join File.dirname(src), to
          if File.exists? dst
            STDERR.puts "Destination already exists: #{dst}"
            exit(-1)
          end

          puts "Moving #{src} → #{dst}"
          FileUtils.mv src, dst
        end
      end

      command :show do |c|
        c.syntax = 'a2km show <spec>'
        c.description = 'Show info about a kernelspec'
        c.action do |args, options|
          name = args.first
          kernel = A2KM.get_kernel(name)
          spec = kernel['spec']
          puts "Kernel: #{name} (#{spec['display_name']})"
          puts "  path: #{kernel['resources_dir']}"
          puts "  argv: #{spec['argv'].join(' ')}"
        end
      end

      command :locate do |c|
        c.syntax = 'a2km locate <spec>'
        c.description = 'Print the path of a kernelspec'
        c.action do |args, options|
          puts A2KM.get_kernel(args.first)['resources_dir']
        end
      end

      command :"add-argv" do |c|
        c.syntax = 'a2km add-argv <spec> <arg1> [arg2] ...'
        c.description = 'Add argument(s) to a kernelspec launch command'
        c.action do |args, options|
          name = args.shift
          kernelspec = A2KM.get_kernel_json(name)
          kernelspec['argv'] += args
          A2KM.save_kernel_json(name, kernelspec)
          puts "New argv: #{kernelspec['argv'].join(' ')}"
        end
      end

      command :"rm-argv" do |c|
        c.syntax = 'a2km rm-argv <spec> <arg1> [arg2] ...'
        c.summary = 'Remove arguments from a kernelspec launch command'
        c.description = c.summary + ". To remove args starting with '-'," \
          " use '--'."
        c.examples = [
          "a2km rm-argv myspec x",
          "a2km rm-argv myspec -- --debug",
        ]
        c.action do |args, options|
          name = args.shift
          to_remove = args
          kernelspec = A2KM.get_kernel_json(name)
          argv = kernelspec['argv']
          argv.reject! { |arg| to_remove.include? arg }
          A2KM.save_kernel_json(name, kernelspec)
          puts "New argv: #{argv.join(' ')}"
        end
      end

      command :"add-env" do |c|
        c.syntax = 'a2km add-env <spec> <key=value> [key=value] ...'
        c.summary = 'Add environment variables to a kernelspec'
        c.description = 'Add environment variables to a kernelspec.' \
          ' If no value is given, the value from the current env is used.'
        c.action do |args, options|
          name = args.shift
          spec = A2KM.get_kernel_json(name)
          if not spec.has_key? 'env'
            spec['env'] = {}
          end
          env = spec['env']
          args.each do |arg|
            key_value = arg.split('=', 2)
            key = key_value.first
            if key_value.length == 2
              value = key_value[1]
            else
              value = ENV[key]
            end
            env[key] = value
          end
          A2KM.save_kernel_json(name, spec)
          puts "New env: #{env}"
        end
      end

      command :"rm-env" do |c|
        c.syntax = 'a2km rm-env <spec> <key> [key] ...'
        c.description = 'Remove environment variables from a kernelspec'
        c.action do |args, options|
          name = args.shift
          spec = A2KM.get_kernel_json(name)
          if not spec.has_key? 'env'
            spec['env'] = {}
          end
          env = spec['env']
          args.each do |arg|
            env.delete(arg)
          end
          A2KM.save_kernel_json(name, spec)
          puts "New env: #{env}"
        end
      end

      command :rm do |c|
        c.syntax = 'a2km rm <spec>'
        c.description = 'Remove a kernelspec'
        c.option '-f', "Force removal (skip confirmation)"
        c.action do |args, options|
          name = args.shift
          if not A2KM.kernels.has_key? name
            STDERR.puts "No such kernel: #{name}"
            STDERR.puts "Found kernels: #{kernels.keys.sort.join(' ')}"
            exit(-1)
          end
          path = A2KM.kernels[name]['resources_dir']
          if options.f or not HighLine.agree("Permanently delete #{path}? (yes/no)")
            STDERR.puts "Aborting."
            exit(-1)
          end
          puts "Removing #{path}"
          FileUtils.rm_r path
        end
      end

      command :"env-kernel" do |c|
        c.syntax = 'a2km env-kernel [--venv|--conda] <name> [-e env-name] [--user]'
        c.description = 'Create a kernel from an env (conda or virtualenv)'
        
        c.option '--conda', "use conda env (default)"
        c.option '--venv', "use virtualenv"
        c.option '-e ENV', "specify the environment name to use (if different from <name>)"
        c.option '--user', "do a user install"
        c.action do |args, options|
          name = args.shift
          options.default :user => false
          options.default :e => name
          env = options.e
          
          kind = 'conda'
          if options.venv
            kind = 'venv'
          end
          puts "Making kernel '#{name}' for #{kind}:#{env}"
          spec = A2KM::make_env_kernel(name, env, kind: kind, user: options.user)
        end
      end

      command :set do |c|
        c.syntax = 'a2km set <name> <key> <value>'
        c.description = 'Set a value in the kernelspec'
        c.examples = [
          'a2km set python3 display_name "My Python 3"'
        ]
        c.action do |args, options|
          name = args.shift
          key = args.shift
          value = args.shift
          if value.nil?
            STDERR.puts c.syntax
            exit(-1)
          end
          puts "Setting #{name}.#{key} = '#{value}'"
          spec = A2KM.get_kernel_json(name)
          spec[key] = value
          A2KM.save_kernel_json(name, spec)
        end
      end

      command :clone do |c|
        c.syntax = 'a2km clone <from> <to> [display_name]'
        c.summary = 'Clone a kernelspec'
        c.description = 'Clones kernelspec FROM to TO'
        c.option '--user', 'Force clone to be in the user directory' \
          ' (default is to use the same directory as FROM)'
        c.action do |args, options|
          options.default :user => false

          if args.length < 2 or args.length > 3
            STDERR.puts "Must specify FROM and TO"
            exit(-1)
          end
          from_name = args.shift
          to_name = args.shift
          if args.length > 0
            display_name = args.shift
          else
            display_name = to_name
          end

          from = A2KM.get_kernel(from_name)
          src = from['resources_dir']

          if options.user?
            dst_dir = A2KM.user_kernel_dir
            makedirs(dst_dir)
          else
            dst_dir = File.dirname src
          end
          dst = File.join dst_dir, to_name
          if File.exists? dst
            STDERR.puts "Destination already exists: #{dst}"
            exit(-1)
          end

          puts "Cloning #{src} → #{dst}"
          FileUtils.cp_r src, dst
          kernel_json = File.join(dst, 'kernel.json')
          kernelspec = File.open(kernel_json) do |f|
            JSON.parse f.read
          end
          kernelspec['display_name'] = display_name
          File.open(kernel_json, 'w') do |f|
            f.write JSON.pretty_generate(kernelspec)
          end
        end
      end

      run!
    end
  end
end
