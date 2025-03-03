require File.dirname(__FILE__) + '/lib/a2km/version'
require 'date'

Gem::Specification.new do |s|
  s.require_paths = ["lib"]
  s.name        = 'a2km'
  s.version     = A2KM::VERSION
  s.date        = Date.today.to_s
  s.summary     = 'Assistant to the Kernel Manager'
  s.description = 'Working with Juptyer kernels'
  s.authors     = ['Min RK']
  s.email       = 'benjaminrk@gmail.com'
  s.homepage    = 'http://github.com/minrk/a2km'
  s.license     = 'BSD'
  s.executables = ['a2km']
  s.files       = `git ls-files`.split($/)
  s.require_paths = %w(lib)
  s.add_runtime_dependency 'commander'
  s.add_runtime_dependency 'highline'
  s.add_runtime_dependency 'liquid'
end
