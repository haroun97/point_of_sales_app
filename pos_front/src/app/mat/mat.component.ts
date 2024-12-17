import { Component, OnInit } from '@angular/core';
import { Matchy } from 'src/libs/matchy/src/main';
import { Condition } from 'src/libs/matchy/src/models/classes/condition';
import { Option } from 'src/libs/matchy/src/models/classes/option';
import { Comparer } from 'src/libs/matchy/src/models/enums/comparer';
import { ConditonProperty } from 'src/libs/matchy/src/models/enums/conditon_property';
import { FieldType } from 'src/libs/matchy/src/models/enums/field_type';


@Component({
  selector: 'app-mat',
  imports: [],
  templateUrl: './mat.component.html',
  styleUrl: './mat.component.css'
})

export class MatComponent implements OnInit {
  title = 'matchy_test';

  ngOnInit() {
    const options = [
      new Option("First Name", "first_name", true, FieldType.string, [
        new Condition(ConditonProperty.length, 20, Comparer.gte),
        new Condition(ConditonProperty.length, 30, Comparer.lt, "not safe choice"),
      ]),
      new Option("Last Name", "last_name", true, FieldType.string, [
        new Condition(ConditonProperty.value, ["AA", "BB"], Comparer.in)
      ]),
      new Option("Age", "age", true, FieldType.integer, [
        new Condition(ConditonProperty.value, 0, Comparer.gte),
        new Condition(ConditonProperty.value, 40, Comparer.lte),
      ]),
      new Option("Registration Number", "registration_num", true, FieldType.string, [
        new Condition(ConditonProperty.regex, '^\\d{8}-\\d{2}$'),
      ]),
      new Option("%", "percentage", true, FieldType.float, [
        new Condition(ConditonProperty.value, 0, Comparer.gte),
        new Condition(ConditonProperty.value, 100, Comparer.lte),
      ]),
    ];

    const matchy = new Matchy(options);
    document.getElementById("matchy")?.appendChild(matchy);

    // Submit method should be overriden to implemnt your logic 
    matchy.submit = async(data:any) => {
      // use data and send it to your api
    };
  }
}