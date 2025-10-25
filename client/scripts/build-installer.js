// scripts/build-installer.js
const {execSync} = require("child_process");
const fs = require("fs");
const path = require("path");

const nodeModulesPath = path.join(__dirname, "../node_modules");
const imgPath = path.join(nodeModulesPath, "@img");
const sharpPath = path.join(nodeModulesPath, "sharp");
const imgBackupPath = path.join(__dirname, "../@img_backup");
const sharpBackupPath = path.join(__dirname, "../sharp_backup");
const packageJsonPath = path.join(__dirname, "../package.json");
const packageJsonBackupPath = path.join(__dirname, "../package.json.backup");

console.log("🚀 Starting installer build process...\n");

let packageJsonRestored = false;

try {
    // Step 1: Backup and patch package.json (remove sharp dependency)
    console.log("📝 Patching package.json...");
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));
    fs.writeFileSync(packageJsonBackupPath, JSON.stringify(packageJson, null, 2));

    // Remove sharp from dependencies
    if (packageJson.dependencies && packageJson.dependencies.sharp) {
        delete packageJson.dependencies.sharp;
        fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
        console.log("✅ Removed sharp from package.json");
    }

    // Step 2: Backup @img and sharp folders temporarily
    console.log("📦 Temporarily moving @img and sharp folders...");
    if (fs.existsSync(imgPath)) {
        fs.renameSync(imgPath, imgBackupPath);
        console.log("✅ @img moved to @img_backup");
    }
    if (fs.existsSync(sharpPath)) {
        fs.renameSync(sharpPath, sharpBackupPath);
        console.log("✅ sharp moved to sharp_backup\n");
    }

    // Step 3: Run electron-builder
    console.log("🔧 Building installer with electron-builder...");
    execSync("npx electron-builder --win --x64", {
        stdio: "inherit",
        cwd: path.join(__dirname, ".."),
    });

    console.log("\n✅ Installer built successfully!");
} catch (error) {
    console.error("\n❌ Build failed:", error.message);
    process.exit(1);
} finally {
    // Restore package.json first
    if (fs.existsSync(packageJsonBackupPath)) {
        console.log("\n📝 Restoring package.json...");
        fs.copyFileSync(packageJsonBackupPath, packageJsonPath);
        fs.unlinkSync(packageJsonBackupPath);
        packageJsonRestored = true;
        console.log("✅ package.json restored");
    }

    // Restore @img and sharp folders
    if (fs.existsSync(imgBackupPath)) {
        console.log("📦 Restoring @img folder...");
        if (fs.existsSync(imgPath)) {
            fs.rmSync(imgPath, {recursive: true, force: true});
        }
        fs.renameSync(imgBackupPath, imgPath);
        console.log("✅ @img restored");
    }
    if (fs.existsSync(sharpBackupPath)) {
        console.log("📦 Restoring sharp folder...");
        if (fs.existsSync(sharpPath)) {
            fs.rmSync(sharpPath, {recursive: true, force: true});
        }
        fs.renameSync(sharpBackupPath, sharpPath);
        console.log("✅ sharp restored");
    }
}

console.log("\n========================================");
console.log("  BUILD COMPLETE!");
console.log("========================================");
console.log("\nInstaller location: dist\\FB OTP Generator-0.1.0-Setup.exe\n");
