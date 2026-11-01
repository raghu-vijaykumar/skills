param([string]$InstallRoot = (Join-Path $HOME '.cache\content-studio\whisper\v1.9.4'))
$ErrorActionPreference = 'Stop'
# Keep the binary and the multilingual model together so a draft uses one reviewed version.
$root = [IO.Path]::GetFullPath($InstallRoot)
$source = Join-Path $root 'source'
$build = Join-Path $root 'build'
$bin = Join-Path $root 'bin'
$models = Join-Path $root 'models'
$cli = Join-Path $bin 'whisper-cli.exe'
$model = Join-Path $models 'ggml-small.bin'
New-Item -ItemType Directory -Force -Path $root,$bin,$models | Out-Null
if (-not (Test-Path -LiteralPath $source)) {
  & git clone --quiet --depth 1 --branch v1.9.4 https://github.com/ggml-org/whisper.cpp.git $source
  if ($LASTEXITCODE -ne 0) { throw 'Could not clone whisper.cpp v1.9.4' }
}
$tag = (& git -C $source describe --tags --exact-match 2>$null)
if ($LASTEXITCODE -ne 0 -or $tag.Trim() -ne 'v1.9.4') { throw 'Local whisper.cpp source is not v1.9.4' }
if (-not (Test-Path -LiteralPath $cli)) {
  & cmake -S $source -B $build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF *> (Join-Path $root 'cmake-configure.log')
  if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed; install the Visual Studio C++ workload and Windows SDK, then inspect cmake-configure.log' }
  & cmake --build $build --config Release --target whisper-cli *> (Join-Path $root 'cmake-build.log')
  if ($LASTEXITCODE -ne 0) { throw 'CMake build failed; inspect cmake-build.log' }
  $built = @((Join-Path $build 'bin\Release\whisper-cli.exe'), (Join-Path $build 'bin\whisper-cli.exe')) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  if (-not $built) { throw 'whisper-cli.exe was not produced' }
  Copy-Item -LiteralPath $built -Destination $cli
  Get-ChildItem -LiteralPath (Split-Path $built) -Filter '*.dll' | Copy-Item -Destination $bin
}
if (-not (Test-Path -LiteralPath $model)) {
  Invoke-WebRequest -Uri 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin' -OutFile $model
}
$actual = (Get-FileHash -LiteralPath $model -Algorithm SHA1).Hash.ToLowerInvariant()
if ($actual -ne '55356645c2b361a969dfd0ef2c5a50d530afd8d5') { throw "Multilingual small model checksum mismatch: $actual" }
Write-Output "whisper.cpp v1.9.4 ready: $cli"
Write-Output "multilingual small model verified: $model"
