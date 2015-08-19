Gem::Specification.new do |s|
  s.name        = 'a2km'
  s.version     = '0.0.1'
  s.date        = '2015-08-18'
  s.summary     = 'Assistant to the Kernel Manager'
  s.description = 'Working with Juptyer kernels'
  s.authors     = ['Min RK']
  s.email       = 'benjaminrk@gmail.com'
  s.homepage    = 'http://github.com/minrk/a2km'
  s.license     = 'BSD'
  s.executables = ['a2km']
  s.requirements = [
    'commander',
    'highline',
  ]
end