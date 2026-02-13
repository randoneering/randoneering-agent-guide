# Nix Build Troubleshooting Guide

Reference for diagnosing and fixing common build errors. Load when encountering build failures.

## Hash Mismatch Errors

### Source Hash Mismatch

**Error:**
```
error: hash mismatch in fixed-output derivation
  specified: sha256-AAAA...
  got:       sha256-BBBB...
```

**Causes:**
1. Upstream changed release without version bump
2. Using wrong source (git tag vs tarball)
3. Fetch includes files not in tarball (e.g., .github/)

**Solutions:**
```nix
# 1. Update hash
hash = "sha256-BBBB...";  # Use the "got" hash

# 2. Use lib.fakeHash to get correct hash
hash = lib.fakeHash;
# Build, get real hash, update

# 3. If using fetchFromGitHub, might need to exclude files
src = fetchFromGitHub {
  owner = "...";
  repo = "...";
  rev = "...";
  hash = "...";
  # Sometimes needed:
  # fetchSubmodules = false;
};
```

### Cargo Hash Mismatch

**Error:**
```
error: hash mismatch in fixed-output derivation '/nix/store/...-crates-io.drv'
```

**Cause:** Cargo.lock changed or dependencies updated

**Solution:**
```nix
# Update cargoHash
cargoHash = lib.fakeHash;
# Build to get real hash
cargoHash = "sha256-...";

# Or use cargoLock if you have Cargo.lock
cargoLock = {
  lockFile = ./Cargo.lock;
  outputHashes = {
    "git-dep-0.1.0" = "sha256-...";
  };
};
```

### NPM Hash Mismatch

**Error:**
```
error: hash mismatch in fixed-output derivation '/nix/store/...-deps.drv'
```

**Solution:**
```nix
# Update npmDepsHash
npmDepsHash = lib.fakeHash;
# Build to get real hash
npmDepsHash = "sha256-...";
```

## Dependency Errors

### Missing Library at Runtime

**Error:**
```
error while loading shared libraries: libssl.so.3: cannot open shared object file
```

**Cause:** Missing runtime dependency

**Solution:**
```nix
# Add to buildInputs
buildInputs = [ openssl ];

# Or use autoPatchelfHook for binaries
nativeBuildInputs = [ autoPatchelfHook ];
buildInputs = [ openssl ];
```

### pkg-config Not Finding Library

**Error:**
```
Package openssl was not found in the pkg-config search path.
```

**Solutions:**
```nix
# 1. Add to nativeBuildInputs AND buildInputs
nativeBuildInputs = [ pkg-config ];
buildInputs = [ openssl ];

# 2. Check pkg-config can find it
env = {
  PKG_CONFIG_PATH = "${openssl.dev}/lib/pkgconfig";
};

# 3. For cross-compilation
PKG_CONFIG_PATH = lib.makeSearchPathOutput "dev" "lib/pkgconfig" buildInputs;
```

### Header Files Not Found

**Error:**
```
fatal error: openssl/ssl.h: No such file or directory
```

**Solutions:**
```nix
# 1. Use .dev output
buildInputs = [ openssl.dev ];

# 2. Add include path manually
env = {
  CPATH = "${openssl.dev}/include";
};

# 3. For Rust bindgen
BINDGEN_EXTRA_CLANG_ARGS = "-I${openssl.dev}/include";
```

## Rust-Specific Errors

### Cargo Build Fails - Target Issues

**Error:**
```
error: failed to run custom build command for `openssl-sys`
```

**Solutions:**
```nix
# 1. Set environment variables
env = {
  OPENSSL_DIR = "${openssl.dev}";
  OPENSSL_LIB_DIR = "${lib.getLib openssl}/lib";
  OPENSSL_INCLUDE_DIR = "${openssl.dev}/include";
};

# 2. Use pkg-config
nativeBuildInputs = [ pkg-config ];
buildInputs = [ openssl ];

# 3. For cross-compilation
CARGO_BUILD_TARGET = stdenv.hostPlatform.rust.rustcTarget;
```

### Cargo Features Not Working

**Error:**
```
error: package `myapp` does not have feature `feature-name`
```

**Solutions:**
```nix
# 1. Check feature exists in Cargo.toml
# 2. Use correct flag syntax
cargoBuildFlags = [ "--features" "feature-name" ];

# Multiple features
cargoBuildFlags = [ "--features" "feat1,feat2" ];

# Or
cargoExtraArgs = "--features feature-name";
```

### Git Dependencies Not Found

**Error:**
```
error: failed to get `package` as a dependency of package `myapp`
```

**Solution:**
```nix
cargoLock = {
  lockFile = ./Cargo.lock;
  outputHashes = {
    "package-0.1.0" = lib.fakeHash;  # Get hash from error, update
  };
};
```

## Python-Specific Errors

### Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'package'
```

**Solutions:**
```nix
# 1. Add to dependencies
dependencies = [ requests ];

# 2. Add to propagatedBuildInputs (old style)
propagatedBuildInputs = [ requests ];

# 3. Check pythonImportsCheck
pythonImportsCheck = [ "package" ];
```

### Build System Issues

**Error:**
```
error: Multiple top-level packages discovered
```

**Solution:**
```nix
# Use pyproject = true for modern packages
pyproject = true;
build-system = [ setuptools ];  # or hatchling, poetry-core

# Or explicitly set format
format = "pyproject";  # or "setuptools", "wheel"
```

### setuptools Not Found

**Error:**
```
ModuleNotFoundError: No module named 'setuptools'
```

**Solution:**
```nix
# Add to build-system (new)
build-system = [ setuptools ];

# Or nativeBuildInputs (old)
nativeBuildInputs = [ setuptools ];
```

## Node.js-Specific Errors

### npm install Fails

**Error:**
```
npm ERR! code ELIFECYCLE
```

**Solutions:**
```nix
# 1. Skip install scripts if they fail
npmInstallFlags = [ "--ignore-scripts" ];

# 2. Set node version
nodejs = nodejs_20;

# 3. Custom install phase
installPhase = ''
  npm install --production
  npm run build
'';
```

### Workspace Issues

**Error:**
```
npm ERR! Workspaces not supported
```

**Solution:**
```nix
# Specify workspace
npmWorkspace = "packages/frontend";

# Or install root and workspaces separately
npmInstallFlags = [ "--workspaces" ];
```

## Build Phase Errors

### Build Phase Fails

**Error:**
```
builder for '/nix/store/...' failed with exit code 2
```

**Debug approach:**
```bash
# 1. Keep failed build
nix-build --keep-failed
cd /tmp/nix-build-*/

# 2. Inspect environment
env | grep -i path
ls -la

# 3. Try build steps manually
unpackPhase
cd $sourceRoot
ls -la
```

**Common fixes:**
```nix
# 1. Override build phase
buildPhase = ''
  make -j$NIX_BUILD_CORES
'';

# 2. Add make flags
makeFlags = [ "PREFIX=$(out)" ];

# 3. Disable parallel build if flaky
enableParallelBuilding = false;
```

### Install Phase Fails

**Error:**
```
error: builder for '...' failed with exit code 1
install: cannot create directory '/usr/local'
```

**Solution:**
```nix
# 1. Override install phase
installPhase = ''
  mkdir -p $out/bin
  cp binary $out/bin/
'';

# 2. Use PREFIX
makeFlags = [ "PREFIX=$(out)" ];

# 3. For autotools
configureFlags = [ "--prefix=${placeholder "out"}" ];
```

## Test Failures

### Tests Requiring Network

**Error:**
```
test result: FAILED. 5 passed; 3 failed
```

**Solutions:**
```nix
# 1. Disable tests
doCheck = false;

# 2. Skip specific tests
checkFlags = [
  "--skip test_network"
  "--skip test_integration"
];

# 3. Custom check phase
checkPhase = ''
  cargo test --lib  # Only unit tests
'';

# 4. For Python
pytestFlagsArray = [ "-k" "not network" ];
```

### Tests Failing in Sandbox

**Error:**
```
test failed: cannot access /home
```

**Solutions:**
```nix
# 1. Disable sandbox (last resort)
__noChroot = true;

# 2. Set HOME
preCheck = ''
  export HOME=$TMPDIR
'';

# 3. Skip problematic tests
doInstallCheck = false;
```

## Cross-Compilation Errors

### Wrong Architecture

**Error:**
```
cannot execute binary file: Exec format error
```

**Cause:** Trying to run build-platform binary on host platform

**Solutions:**
```nix
# 1. Ensure tool is in nativeBuildInputs
nativeBuildInputs = [ pkg-config cmake ];  # Run on build platform

# 2. Libraries in buildInputs
buildInputs = [ openssl sqlite ];  # For host platform

# 3. Detect cross-compilation
buildPhase = lib.optionalString (stdenv.buildPlatform != stdenv.hostPlatform) ''
  # Cross-compilation specific steps
'';
```

### Darwin Framework Issues

**Error:**
```
framework 'Security' not found
```

**Solution:**
```nix
# nixpkgs-unstable removed legacy darwin.apple_sdk.frameworks.* references.
# Use the default SDK from stdenv and patch paths with $SDKROOT when needed.

preConfigure = lib.optionalString stdenv.isDarwin ''
  substituteInPlace Makefile \
    --replace-fail "/System/Library/Frameworks" \
                   "$SDKROOT/System/Library/Frameworks"
'';
```

## License and Meta Issues

### Missing mainProgram

**Warning:**
```
warning: Package does not have meta.mainProgram set
```

**Solution:**
```nix
meta = with lib; {
  mainProgram = "executable-name";  # Name of main binary
  # ...
};
```

### Missing Description

**Error:**
```
error: Package meta.description is required
```

**Solution:**
```nix
meta = with lib; {
  description = "Brief description without package name";
  # NOT: "mypackage - A tool for..." 
  # YES: "Tool for doing X"
};
```

## Performance Issues

### Build Takes Too Long

**Solutions:**
```nix
# 1. Enable parallel building
enableParallelBuilding = true;

# 2. Use more cores
makeFlags = [ "-j$NIX_BUILD_CORES" ];

# 3. For Rust, incremental builds
CARGO_BUILD_INCREMENTAL = "true";

# 4. Use crane for cached builds
# (see advanced-patterns.md)
```

### Large Closure Size

**Debug:**
```bash
# Find why packages are in closure
nix path-info -rsh .#package | sort -h
nix why-depends .#package .#large-dependency

# Find references
nix-store -q --references $(nix-build -A package)
```

**Solutions:**
```nix
# 1. Use separate outputs
outputs = [ "out" "dev" "doc" ];

# 2. Remove unnecessary references
disallowedReferences = [ stdenv.cc ];

# 3. Strip binaries
dontStrip = false;
```

## Evaluation Errors

### Infinite Recursion

**Error:**
```
error: infinite recursion encountered
```

**Common causes:**
```nix
# 1. Self-reference without rec
# BAD:
{
  version = "1.0.0";
  pname = "app-${version}";  # Error!
}

# GOOD:
rec {
  version = "1.0.0";
  pname = "app-${version}";
}

# 2. Circular overlays
# Use lib.composeExtensions carefully
```

### Type Errors

**Error:**
```
error: value is a set while a string was expected
```

**Solution:**
```nix
# Use toString or coercion
port = toString cfg.port;  # Convert int to string

# Check types
lib.isString value
lib.isInt value
lib.isList value
```

## Quick Diagnostic Commands

```bash
# Show derivation
nix show-derivation .#package

# Evaluate specific attribute
nix-instantiate --eval -A package.version '<nixpkgs>'

# Check syntax
nix-instantiate --parse file.nix

# Trace evaluation
nix-build --show-trace -A package

# Check what's in build environment
nix develop .#package
env | sort
```

## Common Patterns for Fixes

### Patch Build System

```nix
postPatch = ''
  # Fix hardcoded paths
  substituteInPlace Makefile \
    --replace '/usr/local' "$out"
  
  # Fix shebang
  patchShebangs scripts/
  
  # Update version
  sed -i 's/version = "0.0.0"/version = "${version}"/' setup.py
'';
```

### Add Missing Files

```nix
preBuild = ''
  # Create missing file
  cat > .env <<EOF
  API_KEY=dummy
  EOF
'';
```

### Disable Unwanted Features

```nix
# CMake
cmakeFlags = [ "-DBUILD_TESTS=OFF" "-DENABLE_DOCS=OFF" ];

# Autotools
configureFlags = [ "--disable-tests" "--without-docs" ];

# Rust
cargoBuildFlags = [ "--no-default-features" "--features" "minimal" ];
```

---

When encountering errors, check this guide for common patterns and solutions.
