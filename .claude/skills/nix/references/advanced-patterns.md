# Advanced Nix Patterns

Load this file when dealing with complex build scenarios, cross-compilation, or advanced flake patterns.

## Cross-Compilation

### Basic Cross-Compilation

```nix
# Build for different architecture
nix build .#package --system aarch64-linux

# In derivation, detect cross-compilation
buildRustPackage {
  # ...
  
  # Only needed when cross-compiling
  CARGO_BUILD_TARGET = if stdenv.hostPlatform != stdenv.buildPlatform
    then stdenv.hostPlatform.rust.rustcTarget
    else null;
  
  # Platform-specific dependencies
  buildInputs = lib.optionals stdenv.isLinux [ systemd ];
}
```

### Cross-Compilation Build Inputs

- `depsBuildBuild`: Tools that run on build platform, produce for build platform
- `nativeBuildInputs`: Tools that run on build platform, produce for host platform (most common)
- `depsBuildTarget`: Tools that run on build platform, produce for target platform
- `depsHostHost`: Libraries for host platform, used by host platform
- `buildInputs`: Libraries for host platform, used by target platform (most common)
- `depsTargetTarget`: Libraries for target platform, used by target platform

### Darwin SDK Pattern (nixpkgs-unstable)

```nix
# Do not use darwin.apple_sdk.frameworks.* on unstable.
# The default SDK is provided by stdenv.

preConfigure = lib.optionalString stdenv.isDarwin ''
  substituteInPlace src/config.h \
    --replace-fail "/System/Library/Frameworks" \
                   "$SDKROOT/System/Library/Frameworks"
'';

# For explicit SDK pinning, use apple-sdk_* packages.
# Example: nativeBuildInputs = [ apple-sdk_13 ];
```

## Advanced Flake Patterns

### Multi-System Flake with Custom Systems

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachSystem [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ] (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages = {
          default = self.packages.${system}.myapp;
          myapp = pkgs.callPackage ./package.nix { };
          myapp-static = pkgs.pkgsStatic.callPackage ./package.nix { };
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.default ];
          packages = with pkgs; [ cargo-edit cargo-watch ];
        };

        checks = {
          build = self.packages.${system}.default;
          test = pkgs.runCommand "test" { } ''
            ${self.packages.${system}.default}/bin/myapp --version
            touch $out
          '';
        };
      }
    );
}
```

### Flake with NixOS Configurations

```nix
{
  outputs = { self, nixpkgs, ... }: {
    nixosConfigurations = {
      hostname = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [
          ./configuration.nix
          self.nixosModules.default
        ];
      };
    };

    nixosModules.default = ./modules/myservice.nix;
    
    # Expose module for others
    nixosModules.myservice = ./modules/myservice.nix;
  };
}
```

### Flake with Multiple Inputs

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";
    crane.url = "github:ipetkov/crane";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, rust-overlay, crane, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ rust-overlay.overlays.default ];
        };
        
        craneLib = crane.mkLib pkgs;
      in
      {
        packages.default = craneLib.buildPackage {
          src = craneLib.cleanCargoSource ./.;
          buildInputs = [ pkgs.openssl ];
        };
      }
    );
}
```

## Build System Specifics

### Meson/Ninja Projects

```nix
{ stdenv, meson, ninja, pkg-config, ... }:

stdenv.mkDerivation {
  pname = "meson-project";
  version = "1.0.0";

  src = ./.;

  nativeBuildInputs = [ meson ninja pkg-config ];
  buildInputs = [ /* libraries */ ];

  mesonFlags = [
    "-Dfeature=enabled"
    "-Ddocs=disabled"
  ];
}
```

### CMake Projects

```nix
{ stdenv, cmake, pkg-config, ... }:

stdenv.mkDerivation {
  pname = "cmake-project";
  version = "1.0.0";

  src = ./.;

  nativeBuildInputs = [ cmake pkg-config ];
  buildInputs = [ /* libraries */ ];

  cmakeFlags = [
    "-DBUILD_TESTING=OFF"
    "-DCMAKE_BUILD_TYPE=Release"
  ];

  # Sometimes needed
  dontUseCmakeConfigure = false;
}
```

### Autotools Projects

```nix
{ stdenv, autoreconfHook, pkg-config, ... }:

stdenv.mkDerivation {
  pname = "autotools-project";
  version = "1.0.0";

  src = ./.;

  nativeBuildInputs = [ autoreconfHook pkg-config ];
  buildInputs = [ /* libraries */ ];

  configureFlags = [
    "--enable-feature"
    "--disable-tests"
  ];

  # If configure.ac needs regeneration
  preConfigure = ''
    autoreconf -fi
  '';
}
```

### Go Projects

```nix
{ lib, buildGoModule, fetchFromGitHub }:

buildGoModule rec {
  pname = "go-project";
  version = "1.0.0";

  src = fetchFromGitHub {
    owner = "owner";
    repo = "repo";
    rev = "v${version}";
    hash = "sha256-...";
  };

  vendorHash = "sha256-...";  # Use lib.fakeHash initially

  # For projects with subpackages
  subPackages = [ "cmd/app1" "cmd/app2" ];

  ldflags = [
    "-s"
    "-w"
    "-X main.version=${version}"
  ];

  meta = with lib; {
    description = "Description";
    homepage = "https://...";
    license = licenses.mit;
    maintainers = with maintainers; [ your-handle ];
    mainProgram = "app1";
  };
}
```

## Advanced Dependency Management

### Rust with Git Dependencies

```nix
buildRustPackage rec {
  pname = "rust-with-git-deps";
  version = "1.0.0";

  src = ./.;

  cargoLock = {
    lockFile = ./Cargo.lock;
    outputHashes = {
      "git-dependency-0.1.0" = "sha256-...";
      "another-git-dep-1.0.0" = "sha256-...";
    };
  };
}
```

### Python with Extra Dependencies

```nix
buildPythonPackage rec {
  pname = "python-app";
  version = "1.0.0";

  src = ./.;

  build-system = [ setuptools ];

  dependencies = [
    requests
    click
  ];

  optional-dependencies = {
    dev = [ pytest black ruff ];
    docs = [ sphinx ];
    all = [ /* all extras */ ];
  };

  # Install specific extras
  passthru.optional-dependencies.dev;
}
```

### Node.js with Workspace Support

```nix
buildNpmPackage rec {
  pname = "npm-monorepo";
  version = "1.0.0";

  src = ./.;

  npmDepsHash = "sha256-...";

  # For workspace/monorepo setups
  npmWorkspace = "packages/frontend";

  # Skip npm install in specific packages
  npmInstallFlags = [ "--ignore-scripts" ];
}
```

## Complex Build Scenarios

### Multi-Stage Builds

```nix
{ stdenv, fetchFromGitHub, rustPlatform, nodejs, ... }:

let
  # Stage 1: Build frontend
  frontend = stdenv.mkDerivation {
    name = "frontend";
    src = ./frontend;
    nativeBuildInputs = [ nodejs ];
    buildPhase = ''
      npm install
      npm run build
    '';
    installPhase = ''
      cp -r dist $out
    '';
  };

  # Stage 2: Build backend with embedded frontend
in rustPlatform.buildRustPackage {
  pname = "fullstack-app";
  version = "1.0.0";

  src = ./.;

  cargoHash = "sha256-...";

  # Embed frontend in backend
  preBuild = ''
    mkdir -p static
    cp -r ${frontend}/* static/
  '';

  meta = { ... };
}
```

### Conditional Features

```nix
{ lib, rustPlatform, enableFeatureX ? true, enableFeatureY ? false, ... }:

rustPlatform.buildRustPackage {
  pname = "app-with-features";
  version = "1.0.0";

  src = ./.;

  cargoHash = "sha256-...";

  cargoBuildFlags = 
    lib.optionals enableFeatureX [ "--features" "feature-x" ]
    ++ lib.optionals enableFeatureY [ "--features" "feature-y" ];

  buildInputs = 
    lib.optionals enableFeatureX [ specialLib ]
    ++ lib.optionals enableFeatureY [ anotherLib ];
}
```

## Testing and CI

### Comprehensive Flake Checks

```nix
{
  outputs = { self, nixpkgs, ... }: {
    checks = nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" ] (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Build check
        build = self.packages.${system}.default;

        # Format check
        format = pkgs.runCommand "check-format" { } ''
          ${pkgs.nixfmt-classic}/bin/nixfmt --check ${self}
          touch $out
        '';

        # Lint check
        lint = pkgs.runCommand "check-lint" { } ''
          ${pkgs.statix}/bin/statix check ${self}
          touch $out
        '';

        # Tests
        test = pkgs.runCommand "test" {
          buildInputs = [ self.packages.${system}.default ];
        } ''
          myapp test
          touch $out
        '';
      }
    );
  };
}
```

### Integration Tests

```nix
{ nixosTest }:

nixosTest {
  name = "myservice-test";
  
  nodes.machine = { pkgs, ... }: {
    imports = [ ./modules/myservice.nix ];
    services.myservice.enable = true;
  };

  testScript = ''
    machine.wait_for_unit("myservice.service")
    machine.wait_for_open_port(8080)
    machine.succeed("curl -f http://localhost:8080/health")
  '';
}
```

## Performance Optimization

### Incremental Builds with Crane

```nix
{ crane, rust, ... }:

let
  craneLib = crane.mkLib pkgs;
  
  # Build dependencies separately
  cargoArtifacts = craneLib.buildDepsOnly {
    src = craneLib.cleanCargoSource ./.;
  };
in
craneLib.buildPackage {
  inherit cargoArtifacts;
  src = craneLib.cleanCargoSource ./.;
}
```

### Cached Builds

```nix
# Add to flake
nixConfig = {
  extra-substituters = [ "https://cache.nixos.org" "https://your-cache.cachix.org" ];
  extra-trusted-public-keys = [ "cache.nixos.org-1:..." "your-cache.cachix.org-1:..." ];
};
```

## Debugging Techniques

### Inspect Build Environment

```nix
# Add to derivation for debugging
DEBUG_BUILD = "1";

buildPhase = ''
  echo "=== Environment Variables ==="
  env | sort
  echo "=== Available Commands ==="
  type -a gcc || true
  type -a pkg-config || true
  echo "=== Library Search Paths ==="
  echo $NIX_LDFLAGS
  echo "=== Compiler Flags ==="
  echo $NIX_CFLAGS_COMPILE
  
  # Actual build
  cargo build --release
'';
```

### Keep Failed Builds

```bash
# Keep build directory on failure
nix-build --keep-failed

# Inspect the failed build
cd /tmp/nix-build-package-1.0.0-*/
ls -la
cat config.log  # For autotools
cat CMakeCache.txt  # For cmake
```

### Interactive Debugging

```bash
# Enter build environment
nix develop .#package

# Or for non-flake
nix-shell '<nixpkgs>' -A package

# Then manually run build steps
unpackPhase
cd $sourceRoot
configurePhase
buildPhase
```

## Common Nixpkgs Patterns

### Split Outputs

```nix
stdenv.mkDerivation {
  pname = "lib-with-dev";
  version = "1.0.0";

  outputs = [ "out" "dev" "doc" ];

  installPhase = ''
    mkdir -p $out/lib $dev/include $doc/share
    cp lib*.so $out/lib/
    cp *.h $dev/include/
    cp -r docs $doc/share/
  '';

  # Other packages can reference:
  # buildInputs = [ lib-with-dev.dev ];
}
```

### Version Passthrough

```nix
{ lib, ... }:

let
  version = "1.0.0";
in
{
  inherit version;
  
  package = stdenv.mkDerivation {
    inherit version;
    pname = "mypackage";
    # ...
  };
  
  # Make version available to consumers
  passthru = {
    inherit version;
    updateScript = ./update.sh;
  };
}
```

### Update Scripts

```nix
passthru.updateScript = writeScript "update.sh" ''
  #!/usr/bin/env nix-shell
  #!nix-shell -i bash -p curl jq common-updater-scripts

  set -eu -o pipefail

  latest_version=$(curl -s https://api.github.com/repos/owner/repo/releases/latest | jq -r .tag_name | sed 's/^v//')
  
  update-source-version ${pname} "$latest_version"
'';
```

---

Use these patterns when dealing with complex build scenarios, cross-compilation, or advanced packaging requirements.
