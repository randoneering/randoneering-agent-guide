# Nix Packaging Project

## Project Context

**Project Name:** [Package/Module Name]

**Description:** [What this package/configuration does]

**Targets:**
- NixOS (Linux)
- nix-darwin (macOS)
- Home Manager (cross-platform user config)

---

## Project Structure

### Flake-based Package

```
├── flake.nix              # Main entry point
├── flake.lock             # Pinned dependencies
├── default.nix            # Compatibility for non-flake users
├── shell.nix              # Dev shell (optional)
├── pkgs/
│   └── mypackage/
│       └── default.nix    # Package derivation
├── modules/
│   ├── nixos/             # NixOS modules
│   └── darwin/            # nix-darwin modules
└── overlays/
    └── default.nix        # Package overlays
```

### System Configuration

```
├── flake.nix
├── hosts/
│   ├── linux-desktop/
│   │   ├── configuration.nix
│   │   └── hardware-configuration.nix
│   └── macbook/
│       └── darwin-configuration.nix
├── modules/
│   ├── common/            # Shared between platforms
│   ├── nixos/             # Linux-specific
│   └── darwin/            # macOS-specific
└── home/
    ├── common.nix         # Shared home-manager
    ├── linux.nix
    └── darwin.nix
```

---

## Flake Basics

### Minimal flake.nix

```nix
{
  description = "My package/configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # Or stable: "github:NixOS/nixpkgs/nixos-24.05"

    # For Darwin
    darwin = {
      url = "github:LnL7/nix-darwin";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # For Home Manager
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, darwin, home-manager, ... }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      packages = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = pkgs.callPackage ./pkgs/mypackage { };
        }
      );

      # NixOS configurations
      nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [ ./hosts/myhost/configuration.nix ];
      };

      # Darwin configurations
      darwinConfigurations.mymac = darwin.lib.darwinSystem {
        system = "aarch64-darwin";
        modules = [ ./hosts/mymac/darwin-configuration.nix ];
      };
    };
}
```

---

## Package Derivations

### Python Package

```nix
# pkgs/mypython/default.nix
{ lib
, python3Packages
, fetchFromGitHub
}:

python3Packages.buildPythonApplication {
  pname = "mypackage";
  version = "1.0.0";

  src = fetchFromGitHub {
    owner = "username";
    repo = "repo";
    rev = "v1.0.0";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  # Or local source
  # src = ./.;

  pyproject = true;

  build-system = with python3Packages; [
    setuptools
  ];

  dependencies = with python3Packages; [
    click
    requests
  ];

  nativeCheckInputs = with python3Packages; [
    pytest
  ];

  checkPhase = ''
    runHook preCheck
    pytest tests/
    runHook postCheck
  '';

  meta = with lib; {
    description = "My Python tool";
    homepage = "https://github.com/username/repo";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
    mainProgram = "mypackage";
  };
}
```

### Rust Package

```nix
# pkgs/myrust/default.nix
{ lib
, rustPlatform
, fetchFromGitHub
, pkg-config
, openssl
}:

rustPlatform.buildRustPackage {
  pname = "mypackage";
  version = "1.0.0";

  src = fetchFromGitHub {
    owner = "username";
    repo = "repo";
    rev = "v1.0.0";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  cargoHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";

  nativeBuildInputs = [ pkg-config ];
  buildInputs = [ openssl ];

  # Skip tests if they need network
  doCheck = false;

  meta = with lib; {
    description = "My Rust tool";
    homepage = "https://github.com/username/repo";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}
```

### Go Package

```nix
{ lib
, buildGoModule
, fetchFromGitHub
}:

buildGoModule {
  pname = "mypackage";
  version = "1.0.0";

  src = fetchFromGitHub {
    owner = "username";
    repo = "repo";
    rev = "v1.0.0";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  vendorHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  # Or if vendor directory is committed:
  # vendorHash = null;

  meta = with lib; {
    description = "My Go tool";
    homepage = "https://github.com/username/repo";
    license = licenses.mit;
  };
}
```

---

## NixOS Modules

```nix
# modules/nixos/myservice.nix
{ config, lib, pkgs, ... }:

let
  cfg = config.services.myservice;
in {
  options.services.myservice = {
    enable = lib.mkEnableOption "my service";

    port = lib.mkOption {
      type = lib.types.port;
      default = 8080;
      description = "Port to listen on";
    };

    user = lib.mkOption {
      type = lib.types.str;
      default = "myservice";
      description = "User to run as";
    };
  };

  config = lib.mkIf cfg.enable {
    users.users.${cfg.user} = {
      isSystemUser = true;
      group = cfg.user;
    };
    users.groups.${cfg.user} = { };

    systemd.services.myservice = {
      description = "My Service";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];

      serviceConfig = {
        ExecStart = "${pkgs.mypackage}/bin/mypackage --port ${toString cfg.port}";
        User = cfg.user;
        Restart = "on-failure";
        RestartSec = 5;
      };
    };

    networking.firewall.allowedTCPPorts = [ cfg.port ];
  };
}
```

---

## nix-darwin Modules

```nix
# modules/darwin/myconfig.nix
{ config, lib, pkgs, ... }:

{
  # System packages
  environment.systemPackages = with pkgs; [
    git
    vim
    ripgrep
  ];

  # Homebrew (for GUI apps not in nixpkgs)
  homebrew = {
    enable = true;
    onActivation.cleanup = "zap";
    casks = [
      "firefox"
      "rectangle"
    ];
  };

  # macOS defaults
  system.defaults = {
    dock = {
      autohide = true;
      mru-spaces = false;
      show-recents = false;
    };

    finder = {
      AppleShowAllExtensions = true;
      FXPreferredViewStyle = "clmv";
    };

    NSGlobalDomain = {
      AppleKeyboardUIMode = 3;
      InitialKeyRepeat = 15;
      KeyRepeat = 2;
    };
  };

  # Keyboard
  system.keyboard = {
    enableKeyMapping = true;
    remapCapsLockToEscape = true;
  };

  # Services (launchd)
  launchd.user.agents.myagent = {
    serviceConfig = {
      ProgramArguments = [ "${pkgs.mypackage}/bin/mypackage" ];
      KeepAlive = true;
      RunAtLoad = true;
    };
  };
}
```

---

## Home Manager

```nix
# home/common.nix
{ config, pkgs, ... }:

{
  home.stateVersion = "24.05";

  home.packages = with pkgs; [
    ripgrep
    fd
    jq
  ];

  programs.git = {
    enable = true;
    userName = "Your Name";
    userEmail = "you@example.com";
    extraConfig = {
      init.defaultBranch = "main";
      push.autoSetupRemote = true;
    };
  };

  programs.zsh = {
    enable = true;
    autosuggestion.enable = true;
    syntaxHighlighting.enable = true;
    shellAliases = {
      ll = "ls -la";
      g = "git";
    };
  };

  programs.starship = {
    enable = true;
    settings = {
      add_newline = false;
    };
  };
}
```

---

## Development Commands

```bash
# Build package
nix build .#mypackage

# Build and run
nix run .#mypackage

# Enter dev shell
nix develop

# Check flake
nix flake check

# Update inputs
nix flake update

# Update single input
nix flake lock --update-input nixpkgs

# Apply NixOS config
sudo nixos-rebuild switch --flake .#myhost

# Apply Darwin config
darwin-rebuild switch --flake .#mymac

# Apply Home Manager
home-manager switch --flake .#myuser
```

---

## Getting Hashes

```bash
# For fetchFromGitHub - use fake hash first, build will show correct one
hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";

# Or use nix-prefetch
nix-prefetch-url --unpack https://github.com/owner/repo/archive/v1.0.0.tar.gz

# For cargoHash/vendorHash - same approach, use fake hash first
# The build error will show the correct hash
```

---

## Cross-Platform Patterns

```nix
# Conditional based on system
{ lib, stdenv, ... }:

{
  # Different packages per platform
  home.packages = with pkgs; [
    # Common
    git
    ripgrep
  ] ++ lib.optionals stdenv.isLinux [
    # Linux only
    xclip
  ] ++ lib.optionals stdenv.isDarwin [
    # macOS only
    pngpaste
  ];
}
```

---

## Common Tasks

### Add Package to Nixpkgs

1. Fork nixpkgs
2. Create `pkgs/by-name/my/mypackage/package.nix`
3. Test locally: `nix-build -A mypackage`
4. Run tests: `nix-build -A mypackage.tests`
5. Submit PR to nixpkgs

### Debug Build Failure

```bash
# Build with verbose output
nix build .#mypackage -L

# Enter build environment
nix develop .#mypackage

# Inside, run phases manually
unpackPhase
cd source
configurePhase
buildPhase
```

### Override Package

```nix
# In overlay or configuration
mypackage = pkgs.mypackage.overrideAttrs (old: {
  version = "2.0.0";
  src = fetchFromGitHub {
    # ...
  };
});
```

---

## Do Not

- Commit `flake.lock` changes without testing
- Use `fetchurl` for GitHub repos (use `fetchFromGitHub`)
- Hardcode paths like `/home/user` (use `$HOME` or `config.home.homeDirectory`)
- Skip `meta` section in packages
- Use `with pkgs;` at module level (breaks lazy evaluation)
- Mix NixOS and Darwin specific options without guards

---

## Verification Before Completion

```bash
# Check flake syntax
nix flake check

# Build all packages
nix build .#mypackage

# Test configuration (dry run)
nixos-rebuild dry-build --flake .#myhost
darwin-rebuild check --flake .#mymac

# Verify it runs
nix run .#mypackage -- --help
```
