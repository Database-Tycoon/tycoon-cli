/**
 * Flat terrain: CPU-baked palette texture.
 *
 * The e2e suite counts exact-colour pixels in this mode, so it must stay
 * byte-predictable — atlas art would make those counts meaningless.
 */

import * as THREE from "three";
import type { CityDocument } from "../contract";
import { decodeRle } from "../contract";
import { GROUND } from "../palette";

const SKIRT_SIZE = 4096;

function buildFlatTerrain(doc: CityDocument): THREE.Group {
  const { width, height, tile_kinds } = doc.grid;
  const cells = decodeRle(doc.grid.tiles_rle, width, height);

  const data = new Uint8Array(width * height * 4);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const kindName = tile_kinds[cells[y * width + x]!] ?? "grass";
      let color = GROUND[kindName] ?? GROUND.grass!;
      // The 2D map's alternating grass parity, carried over so the ground
      // reads as the same city.
      if (kindName === "grass" && (x + y) % 2 !== 0) color = GROUND.grass_alt!;
      // Texture row `height - 1 - y`: PlaneGeometry's v=0 edge lands on the
      // +z side after the -90° X rotation, so grid rows are stored bottom-up
      // to put tile (x, y) at world (x, 0, y). Storing them top-down mirrors
      // the whole city north-south -- the district labels are the visual
      // check that this is right.
      const at = ((height - 1 - y) * width + x) * 4;
      // THREE.Color stores linear floats (colour management converts hex on
      // construction), but this texture is tagged sRGB, so the bytes written
      // must be sRGB-encoded -- writing the linear floats raw renders the whole
      // grid visibly darker than the skirt next to it. Caught by eye, exactly
      // the class of bug the render-and-look rule exists for.
      const srgb = color.clone().convertLinearToSRGB();
      data[at] = Math.round(srgb.r * 255);
      data[at + 1] = Math.round(srgb.g * 255);
      data[at + 2] = Math.round(srgb.b * 255);
      data[at + 3] = 255;
    }
  }

  const texture = new THREE.DataTexture(data, width, height, THREE.RGBAFormat);
  texture.magFilter = THREE.NearestFilter;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.generateMipmaps = true;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;

  const grid = new THREE.Mesh(
    new THREE.PlaneGeometry(width, height),
    new THREE.MeshBasicMaterial({ map: texture }),
  );
  grid.rotateX(-Math.PI / 2);
  grid.position.set(width / 2, 0, height / 2);

  const skirt = new THREE.Mesh(
    new THREE.PlaneGeometry(SKIRT_SIZE, SKIRT_SIZE),
    new THREE.MeshBasicMaterial({ color: GROUND.grass_alt }),
  );
  skirt.rotateX(-Math.PI / 2);
  skirt.position.set(width / 2, -0.02, height / 2);

  const group = new THREE.Group();
  group.add(grid, skirt);
  return group;
}

export { buildFlatTerrain };
